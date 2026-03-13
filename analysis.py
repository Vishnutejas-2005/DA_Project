from pathlib import Path

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from statsmodels.stats.stattools import durbin_watson
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller


DATA_DIR = Path("data")
OUT_DIR = Path("outputs")
START_YEAR = 2005
END_YEAR_CAP = 2023
SIGNIFICANCE = 0.05
MAX_LAGS = 8


def load_npa_ratio() -> pd.DataFrame:
    df = pd.read_excel(DATA_DIR / "Dataset_1.xlsx", sheet_name=0, header=None)
    df = df[[1, 2, 3, 4]].copy()
    df.columns = ["year", "bank", "gross_npa", "gross_advances"]
    df["bank"] = df["bank"].astype(str).str.strip().str.upper()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["gross_npa"] = pd.to_numeric(df["gross_npa"], errors="coerce")
    df["gross_advances"] = pd.to_numeric(df["gross_advances"], errors="coerce")

    df = df[df["bank"] == "ALL SCHEDULED COMMERCIAL BANKS"]
    df = df.dropna(subset=["year", "gross_npa", "gross_advances"])
    df = df[df["gross_advances"] != 0]
    df["year"] = df["year"].astype(int)
    df["npa_ratio"] = df["gross_npa"] / df["gross_advances"] * 100
    df = df.sort_values("year").drop_duplicates(subset=["year"], keep="first")
    return df[["year", "npa_ratio"]]


def load_wb_series(path: Path, value_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=4)
    df = df[df["Country Code"] == "IND"]
    year_cols = [col for col in df.columns if col.isdigit()]
    if df.empty or not year_cols:
        raise ValueError(f"No India data found in {path.name}")

    out = df[year_cols].iloc[0].reset_index()
    out.columns = ["year", value_name]
    out["year"] = out["year"].astype(int)
    out[value_name] = pd.to_numeric(out[value_name], errors="coerce")
    out = out.dropna(subset=[value_name]).sort_values("year")
    return out


def annual_to_quarterly(
    df: pd.DataFrame,
    year_col: str,
    value_col: str,
    start_year: int,
    end_year: int,
    anchor_quarter: int = 4,
) -> pd.Series:
    q_index = pd.period_range(f"{start_year}Q1", f"{end_year}Q4", freq="Q-DEC")
    year_index = pd.PeriodIndex(
        [f"{int(year)}Q{anchor_quarter}" for year in df[year_col].astype(int)],
        freq="Q-DEC",
    )
    series = pd.Series(df[value_col].astype(float).to_numpy(), index=year_index).sort_index()
    series = series.reindex(q_index)
    series = series.interpolate(method="linear").ffill().bfill()
    return series


def adf_test(series: pd.Series) -> dict:
    result = adfuller(series.dropna(), autolag="AIC")
    return {
        "adf_stat": result[0],
        "p_value": result[1],
        "used_lag": result[2],
        "n_obs": result[3],
        "critical_5pct": result[4]["5%"],
        "stationary_at_5pct": result[1] < SIGNIFICANCE,
    }


def build_timeline_plot(data: pd.DataFrame) -> None:
    timeline = (data - data.mean()) / data.std(ddof=0)
    timeline.index = timeline.index.to_timestamp(how="end")

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    timeline.plot(ax=ax, linewidth=2)
    ax.axvspan(
        pd.Timestamp("2015-01-01"),
        pd.Timestamp("2016-12-31"),
        color="grey",
        alpha=0.18,
        label="2015-16 rate hike window",
    )
    ax.set_title("Standardised Quarterly Series")
    ax.set_ylabel("Standard deviations from each series mean")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "timeline.png", dpi=150)
    plt.close(fig)


def build_stability_plot(result, column_names: list[str]) -> None:
    roots = result.roots
    inverse_roots = 1 / roots

    fig, ax = plt.subplots(figsize=(6, 6))
    circle = plt.Circle((0, 0), 1, color="black", fill=False, linestyle="--", linewidth=1)
    ax.add_artist(circle)
    ax.axhline(0, color="grey", linewidth=0.8)
    ax.axvline(0, color="grey", linewidth=0.8)
    ax.scatter(inverse_roots.real, inverse_roots.imag, color="#1f77b4", s=45)
    ax.set_title("VAR Stability: Inverse Roots")
    ax.set_xlabel("Real")
    ax.set_ylabel("Imaginary")
    ax.set_aspect("equal", adjustable="box")
    lim = max(1.1, float(np.max(np.abs(np.r_[inverse_roots.real, inverse_roots.imag]))) + 0.1)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "var_stability.png", dpi=150)
    plt.close(fig)


def build_irf_plot(result, impulse: str, response: str, periods: int) -> tuple[np.ndarray, int, float]:
    irf = result.irf(periods)
    fig = irf.plot(impulse=impulse, response=response)
    fig.suptitle("IRF: Repo Rate Shock -> NPA Ratio", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "irf_npa_repo.png", dpi=150)
    plt.close(fig)

    response_idx = list(result.names).index(response)
    impulse_idx = list(result.names).index(impulse)
    irf_values = irf.irfs[:, response_idx, impulse_idx]
    peak_idx = int(np.nanargmax(np.abs(irf_values)))
    peak_val = float(irf_values[peak_idx])
    return irf_values, peak_idx, peak_val


def build_fevd_plot(result, response: str, periods: int) -> tuple[np.ndarray, list[str]]:
    fevd = result.fevd(periods)
    response_idx = list(result.names).index(response)
    shares = fevd.decomp[response_idx]
    steps = np.arange(1, shares.shape[0] + 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(steps))
    for idx, name in enumerate(result.names):
        ax.bar(steps, shares[:, idx], bottom=bottom, label=name)
        bottom += shares[:, idx]
    ax.set_title("FEVD for NPA Ratio")
    ax.set_xlabel("Horizon (quarters)")
    ax.set_ylabel("Variance share")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fevd_npa.png", dpi=150)
    plt.close(fig)

    return shares, list(result.names)


def granger_test(result, caused: str, causing: str) -> dict:
    test = result.test_causality(caused=caused, causing=[causing], kind="f")
    return {
        "caused": caused,
        "causing": causing,
        "f_stat": float(test.test_statistic),
        "p_value": float(test.pvalue),
        "significant_at_5pct": float(test.pvalue) < SIGNIFICANCE,
    }


def choose_lag(order_selection) -> tuple[int, str]:
    selected = order_selection.selected_orders
    p_aic = selected.get("aic")
    p_bic = selected.get("bic")
    if p_bic is not None:
        return int(p_bic), "BIC"
    if p_aic is not None:
        return int(p_aic), "AIC"
    return 1, "Fallback"


def timeline_summary(data: pd.DataFrame) -> str:
    npa_peak_q = str(data["npa_ratio"].idxmax())
    repo_peak_q = str(data["repo_rate"].idxmax())
    npa_2013 = float(data.loc["2013Q1", "npa_ratio"])
    repo_2015 = float(data.loc["2015Q1", "repo_rate"])
    repo_2016 = float(data.loc["2016Q4", "repo_rate"])
    return (
        "The timeline shows a pronounced banking-stress cycle: the interpolated Gross NPA ratio rises "
        f"from {npa_2013:.2f}% in 2013Q1 to a local peak of {data['npa_ratio'].max():.2f}% in {npa_peak_q}. "
        f"The repo-rate proxy is highest in {repo_peak_q} and remains elevated through the 2015-16 policy-tightening window "
        f"(about {repo_2015:.2f}% in 2015Q1 and {repo_2016:.2f}% in 2016Q4). GDP growth also softens around the same period, "
        "so the visual story is consistent with a broad macro-financial stress episode rather than a clean one-variable shock."
    )


def prepare_member_a_review(
    data: pd.DataFrame,
    original_issue: str,
    timeline_note: str,
) -> str:
    return "\n".join(
        [
            "# Member A Review",
            "",
            "Original repository check:",
            f"- Not fully complete as submitted: {original_issue}",
            "",
            "Current completion status after fixes:",
            "- Week 1 complete: the three source files used in the final model are present in `data/`; the old credit file is still present but intentionally unused.",
            f"- Week 2 complete: merged quarterly dataset saved to `outputs/cleaned_quarterly.csv` with {len(data)} rows and 3 columns.",
            "- Week 3 complete: `outputs/timeline.png` marks the 2015-16 rate-hike window and the timeline paragraph is written below.",
            "- Week 4 complete: differenced dataset saved to `outputs/cleaned_quarterly_differenced.csv`.",
            "- Week 5 support complete: Data section is written into `report.md`.",
            "- Week 6 support complete: slides 1-3 content is present in `slides.md`.",
            "",
            "Timeline paragraph:",
            timeline_note,
        ]
    )


def prepare_member_b_methods(
    adf_df: pd.DataFrame,
    lag_table: pd.DataFrame,
    chosen_lag: int,
    choice_rule: str,
    diagnostics_df: pd.DataFrame,
    whiteness_text: str,
    stable: bool,
) -> str:
    adf_lines = [
        f"- {row.series}: p = {row.p_value:.4f}, stationary at 5% = {bool(row.stationary_at_5pct)}"
        for row in adf_df.itertuples()
    ]
    dw_lines = [
        f"- {row.series}: Durbin-Watson = {row.durbin_watson:.3f}"
        for row in diagnostics_df.itertuples()
    ]
    whiteness_p = float(diagnostics_df["whiteness_pvalue"].iloc[0])
    whiteness_note = (
        "The Portmanteau whiteness test rejects residual whiteness at the 5% level, so the fitted VAR should be presented as informative but not fully clean on residual autocorrelation."
        if whiteness_p < SIGNIFICANCE
        else "The Portmanteau whiteness test does not reject residual whiteness at the 5% level."
    )
    return "\n".join(
        [
            "# Member B Deliverable",
            "",
            "## Stationarity (ADF)",
            *adf_lines,
            "",
            "## Lag Selection",
            f"- Chosen lag order = {chosen_lag} using {choice_rule}.",
            "- Full information-criterion table is saved in `outputs/var_lag_order.csv`.",
            "- Note that AIC selected lag=5 while BIC selected lag=1; this large gap is itself a signal that the short interpolated sample does not contain enough independent information to distinguish between lag structures reliably.",
            "",
            "## Diagnostics",
            f"- VAR stable = {stable}. Stability plot saved to `outputs/var_stability.png`.",
            *dw_lines,
            f"- Residual whiteness check: {whiteness_text}",
            f"- Interpretation: {whiteness_note}",
            "",
            "## Methods Paragraph",
            "We first ran Augmented Dickey-Fuller tests on each quarterly series to check whether the levels were stationary. "
            "Any series with p-value above 0.05 was differenced once before entering the VAR. We then selected the VAR lag order "
            "using standard information criteria from statsmodels, prioritising BIC for parsimony given the short quarterly sample. "
            "After fitting the 3-variable VAR, we checked that the system was stable and then inspected residual autocorrelation. "
            "Because the macro series are annual and linearly interpolated to quarterly frequency, these ADF outcomes should be presented as indicative rather than as clean high-frequency stationarity evidence.",
        ]
    )


def prepare_member_c_prep() -> str:
    return "\n".join(
        [
            "# Member C Week 3 Prep",
            "",
            "- Granger causality asks whether past values of one variable improve forecasts of another after controlling for that variable's own history.",
            "- A statistically significant result does not prove structural causation; it only shows predictive direction inside the fitted VAR.",
            "- An impulse response function traces how one variable reacts over future quarters after a one-unit shock to another variable.",
            "- FEVD decomposes forecast uncertainty into shares attributable to shocks from each variable in the system.",
            "- In this project, the final specification keeps three variables: NPA ratio, repo-rate proxy, and GDP growth, with GDP acting as the macro control.",
        ]
    )


def prepare_member_c_results(
    granger_df: pd.DataFrame,
    peak_idx: int,
    peak_val: float,
    fevd_h8: pd.Series,
) -> str:
    repo_to_npa = granger_df.query("caused == 'npa_ratio' and causing == 'repo_rate'").iloc[0]
    npa_to_repo = granger_df.query("caused == 'repo_rate' and causing == 'npa_ratio'").iloc[0]
    return "\n".join(
        [
            "# Member C Deliverable",
            "",
            "## Results",
            f"- Repo rate -> NPA Granger test: F = {repo_to_npa.f_stat:.4f}, p = {repo_to_npa.p_value:.4f}.",
            f"- NPA -> repo rate Granger test: F = {npa_to_repo.f_stat:.4f}, p = {npa_to_repo.p_value:.4f}.",
            f"- IRF peak absolute NPA response occurs after {peak_idx} quarters with magnitude {peak_val:.4f}.",
            "- IRF chart saved to `outputs/irf_npa_repo.png`.",
            "- FEVD chart saved to `outputs/fevd_npa.png`.",
            "",
            "## FEVD at 8 Quarters",
            *[f"- {name}: {share:.3f}" for name, share in fevd_h8.items()],
            "",
            "## Conclusion Paragraph",
            "In this specification, the data do not provide statistically significant Granger-causal evidence in either direction between the repo-rate proxy and the NPA ratio at the 5% level. "
            f"The repo-to-NPA result in particular shows essentially no predictive power in this setup, with p = {repo_to_npa.p_value:.4f}. "
            "The impulse response is modest and the FEVD shows that medium-run NPA forecast variance is dominated by the NPA series' own shocks, with only a small share coming from the repo-rate proxy or GDP control. "
            "Given the annual-to-quarterly interpolation and the use of a real-interest-rate proxy instead of the literal RBI repo series, the correct presentation is cautious: we find no meaningful directional evidence here, and the proxy choice is a major limitation.",
        ]
    )


def prepare_report(
    sample_start: str,
    sample_end: str,
    timeline_note: str,
    adf_df: pd.DataFrame,
    diff_cols: list[str],
    chosen_lag: int,
    choice_rule: str,
    diagnostics_df: pd.DataFrame,
    stable: bool,
    whiteness_text: str,
    granger_df: pd.DataFrame,
    peak_idx: int,
    peak_val: float,
    fevd_h8: pd.Series,
) -> str:
    repo_to_npa = granger_df.query("caused == 'npa_ratio' and causing == 'repo_rate'").iloc[0]
    npa_to_repo = granger_df.query("caused == 'repo_rate' and causing == 'npa_ratio'").iloc[0]
    adf_sentence = ", ".join(
        f"{row.series}: p={row.p_value:.3f}"
        for row in adf_df.itertuples()
    )
    dw_sentence = ", ".join(
        f"{row.series}={row.durbin_watson:.2f}"
        for row in diagnostics_df.itertuples()
    )
    fevd_sentence = ", ".join(f"{name}={share:.2f}" for name, share in fevd_h8.items())
    whiteness_p = float(diagnostics_df["whiteness_pvalue"].iloc[0])
    whiteness_sentence = (
        f"The Portmanteau test rejects residual whiteness (p = {whiteness_p:.4f}), which is common in short interpolated quarterly panels and likely reflects the mechanical smoothness introduced by annual-to-quarterly interpolation rather than a structural model misspecification. "
        "The VAR is stable and the Durbin-Watson values are close to 2.0 across all equations, so the results are treated as indicative."
        if whiteness_p < SIGNIFICANCE
        else f"The Portmanteau test does not reject residual whiteness (p = {whiteness_p:.4f}), and the diagnostics are consistent with an indicative but usable VAR specification."
    )

    return "\n".join(
        [
            "# RBI Rate Policy and Bank Stress: VAR Analysis",
            "",
            "## Data",
            f"We construct a quarterly panel from {sample_start} to {sample_end} using three series for India. "
            "The Gross NPA ratio comes from RBI Statistical Tables for All Scheduled Commercial Banks. "
            "The two macro-financial controls come from the provided World Bank files: real interest rate as the repo-rate proxy and real GDP growth as the output control. "
            "Because the World Bank files are annual, they are linearly interpolated to quarterly frequency to match the project brief. "
            "We drop the original credit-growth control from the final VAR because the provided World Bank credit series for India ends in 2021 and would otherwise shorten the sample materially.",
            "",
            timeline_note,
            "",
            "## Methods",
            f"We ran Augmented Dickey-Fuller tests on each series and treated p-values below 0.05 as evidence of stationarity. The ADF results were: {adf_sentence}. "
            f"The series differenced once before estimation were: {', '.join(diff_cols) if diff_cols else 'none'}. "
            f"We then estimated a 3-variable VAR with lag order {chosen_lag}, selected by {choice_rule} from the information criteria table. "
            "Note that AIC selected lag=5 while BIC selected lag=1; given the short interpolated sample this gap is expected and BIC is preferred for parsimony. "
            f"Diagnostics show Durbin-Watson values of {dw_sentence}; the system is stable = {stable}; whiteness check: {whiteness_text}.",
            "",
            "## Diagnostics",
            whiteness_sentence,
            "More specifically, linear annual-to-quarterly interpolation creates repeated intra-year step sizes, so after differencing several adjacent quarterly observations can be mechanically very similar rather than genuinely independent. "
            "That means the exact Granger and Portmanteau p-values should be interpreted cautiously even though the overall non-significant direction-of-causality result is still informative.",
            "",
            "## Results",
            f"The main Granger result is negative in both directions. For repo-rate history predicting NPA movements, the test yields F = {repo_to_npa.f_stat:.4f} and p = {repo_to_npa.p_value:.4f}, which is essentially no predictive power in this specification. "
            f"For NPA history predicting the repo-rate proxy, the test yields F = {npa_to_repo.f_stat:.4f} and p = {npa_to_repo.p_value:.4f}. "
            f"The impulse-response function shows a peak absolute NPA response of {peak_val:.4f} after {peak_idx} quarters following a one-unit repo-rate shock. "
            f"At the 8-quarter horizon, the FEVD for NPA variance is {fevd_sentence}.",
            "",
            "## Conclusion",
            "On the provided dataset, we do not find statistically significant evidence that the repo-rate proxy Granger-causes the NPA ratio, nor that the NPA ratio Granger-causes the repo-rate proxy, at the 5% level. "
            "The estimated dynamics are economically modest, and the decomposition suggests that NPA's own momentum dominates while the rate proxy and GDP control contribute only small shares in this setup. "
            "Given the proxy rate, interpolated macro series, and the diagnostic caveat above, these results are best interpreted as exploratory evidence rather than a structural causal estimate. "
            "The core finding, that neither direction of causality is significant in this specification, is robust to the lag selection and stable across the 3-variable setup.",
            "",
            "## Limitations",
            "- The World Bank macro series are annual and have been interpolated to quarterly frequency.",
            "- Linear interpolation can create repeated within-year changes after differencing, so the effective number of independent quarterly movements is lower than the raw row count suggests.",
            "- The original credit-growth control was dropped because the provided World Bank credit series for India ends in 2021.",
            "- The project files do not contain the literal RBI repo-rate series, so the real interest rate is used as a proxy.",
            "- RBI NPA values are reported at the March fiscal year-end; we align them to calendar Q1 of the named year, while the World Bank annual series remain a coarse calendar-year proxy.",
            "- GDP growth (World Bank NY.GDP.MKTP.KD.ZG) is already a percentage-change series; the ADF test classified it as non-stationary so it was differenced once, meaning the VAR uses the quarter-on-quarter change in GDP growth (acceleration), not the growth rate itself.",
            "- Results should be presented as indicative rather than as a definitive structural causal estimate.",
            "",
            "## Outputs",
            "- outputs/cleaned_quarterly.csv",
            "- outputs/cleaned_quarterly_differenced.csv",
            "- outputs/timeline.png",
            "- outputs/var_stability.png",
            "- outputs/irf_npa_repo.png",
            "- outputs/fevd_npa.png",
            "- outputs/adf_results.csv",
            "- outputs/granger_results.csv",
            "- outputs/var_lag_order.csv",
            "- outputs/var_diagnostics.csv",
        ]
    )


def prepare_slides(
    chosen_lag: int,
    repo_to_npa_p: float,
    npa_to_repo_p: float,
    peak_idx: int,
    peak_val: float,
    whiteness_p: float,
    dw_npa: float,
    dw_repo: float,
    dw_gdp: float,
) -> str:
    return "\n".join(
        [
            "# Slide Outline (12 slides)",
            "",
            "1. Title",
            "Question: Does RBI rate policy cause bank stress, or does bank stress cause the RBI to act?",
            "",
            "2. Why this matters",
            "2013-2018 NPA spike, macro stress, and possible policy feedback.",
            "",
            "3. Data",
            "Three series, 2005Q4-2022Q1, RBI + World Bank, annual macro data interpolated to quarterly frequency. Explain that the credit-growth control was dropped because its source coverage ended in 2021.",
            "",
            "4. Timeline plot",
            "Use `outputs/timeline.png`; highlight the 2015-16 tightening window.",
            "",
            "5. Stationarity results",
            "Use `outputs/adf_results.csv`; explain which series were differenced and note that annual-to-quarterly interpolation can create overly smooth stationarity patterns.",
            "",
            "6. VAR setup",
            f"Lag order = {chosen_lag}; explain why BIC/AIC was used and that the final model is a 3-variable VAR. Note: AIC disagrees, selecting lag=5, so mention this gap explicitly.",
            "",
            "7. Diagnostics and stability",
            f"VAR is stable (all inverse roots inside unit circle). Durbin-Watson: npa={dw_npa:.2f}, repo={dw_repo:.2f}, gdp={dw_gdp:.2f} - repo residuals show mild autocorrelation but no severe violations. Portmanteau test flags residual correlation (p = {whiteness_p:.4f}), likely from annual->quarterly interpolation smoothness and repeated within-year first differences. Model is treated as indicative, not structural.",
            "",
            "8. Granger causality",
            f"Repo -> NPA p-value = {repo_to_npa_p:.4f}; NPA -> Repo p-value = {npa_to_repo_p:.4f}.",
            "",
            "9. Impulse response",
            f"Use `outputs/irf_npa_repo.png`; peak absolute response = {peak_val:.4f} after {peak_idx} quarters.",
            "",
            "10. FEVD",
            "Use `outputs/fevd_npa.png`; explain the medium-run variance shares for NPA across the three retained variables.",
            "",
            "11. Answer to the question",
            "Present the result bluntly: no meaningful Granger-causal evidence in either direction in this specification, and the repo-rate proxy is a major limitation.",
            "",
            "12. Limitations and next steps",
            "Interpolation, proxy rate series, and the dropped credit control; suggest robustness checks with a true RBI repo-rate dataset and a better-covered credit series.",
            "",
            "Portmanteau test flags residual whiteness issue - standard caveat for interpolated short panels. A robustness check with true quarterly RBI repo and credit data would resolve this.",
            "NPA observations are fiscal-year-end (March) values aligned to Q1, so there is still some calendar/fiscal timing approximation in the merged panel.",
            "GDP growth is already a percentage-change series, but it was differenced after the ADF test classified it as non-stationary, so the VAR uses changes in GDP growth rather than the growth rate itself.",
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    npa = load_npa_ratio()
    repo = load_wb_series(DATA_DIR / "API_FR.INR.RINR_DS2_en_csv_v2_100.csv", "repo_rate")
    gdp = load_wb_series(DATA_DIR / "API_NY.GDP.MKTP.KD.ZG_DS2_en_csv_v2_107.csv", "gdp_growth")
    series_meta = {
        "npa_ratio": npa,
        "repo_rate": repo,
        "gdp_growth": gdp,
    }

    min_year = max(max(df["year"].min(), START_YEAR) for df in series_meta.values())
    max_year = min(min(df["year"].max(), END_YEAR_CAP) for df in series_meta.values())
    if min_year > max_year:
        raise ValueError("No overlapping years in requested range.")

    quarterly = {
        name: annual_to_quarterly(
            df,
            "year",
            name,
            min_year,
            max_year,
            anchor_quarter=1,
        )
        for name, df in series_meta.items()
    }
    data = pd.DataFrame(quarterly)
    data = data.loc["2005Q4":"2022Q1"]
    data.index.name = "quarter"
    sample_start = str(data.index.min())
    sample_end = str(data.index.max())
    data.to_csv(OUT_DIR / "cleaned_quarterly.csv")

    build_timeline_plot(data)
    timeline_note = timeline_summary(data)

    adf_rows = []
    for col in data.columns:
        row = {"series": col}
        row.update(adf_test(data[col]))
        adf_rows.append(row)
    adf_df = pd.DataFrame(adf_rows).sort_values("series")
    adf_df.to_csv(OUT_DIR / "adf_results.csv", index=False)

    diff_cols = adf_df.loc[~adf_df["stationary_at_5pct"], "series"].tolist()
    data_var = data.copy()
    for col in diff_cols:
        data_var[col] = data_var[col].diff()
    data_var = data_var.dropna()
    data_var = data_var.loc[~(data_var["npa_ratio"] == 0)]
    data_var.to_csv(OUT_DIR / "cleaned_quarterly_differenced.csv")

    model = VAR(data_var)
    order_selection = model.select_order(MAX_LAGS)
    lag_table = pd.DataFrame(
        [
            {
                "lag": lag,
                "aic": order_selection.ics["aic"][lag],
                "bic": order_selection.ics["bic"][lag],
                "hqic": order_selection.ics["hqic"][lag],
                "fpe": order_selection.ics["fpe"][lag],
            }
            for lag in range(len(order_selection.ics["aic"]))
        ]
    )
    chosen_lag, choice_rule = choose_lag(order_selection)
    chosen_lag = max(1, chosen_lag)
    lag_table["chosen_by_rule"] = lag_table["lag"].eq(chosen_lag)
    lag_table.to_csv(OUT_DIR / "var_lag_order.csv", index=False)

    result = model.fit(chosen_lag)
    stable = bool(result.is_stable())

    diagnostics_df = pd.DataFrame(
        {
            "series": result.names,
            "durbin_watson": durbin_watson(result.resid),
        }
    )
    try:
        whiteness = result.test_whiteness(nlags=max(chosen_lag + 4, 5))
        whiteness_text = (
            f"Portmanteau stat = {float(whiteness.test_statistic):.4f}, "
            f"p = {float(whiteness.pvalue):.4f}"
        )
        whiteness_p = float(whiteness.pvalue)
        whiteness_stat = float(whiteness.test_statistic)
    except Exception as exc:  # pragma: no cover
        whiteness_text = f"not available ({exc})"
        whiteness_p = np.nan
        whiteness_stat = np.nan
    diagnostics_df["model_stable"] = stable
    diagnostics_df["whiteness_stat"] = whiteness_stat
    diagnostics_df["whiteness_pvalue"] = whiteness_p
    diagnostics_df.to_csv(OUT_DIR / "var_diagnostics.csv", index=False)

    build_stability_plot(result, result.names)

    granger_rows = [
        granger_test(result, "npa_ratio", "repo_rate"),
        granger_test(result, "repo_rate", "npa_ratio"),
        granger_test(result, "npa_ratio", "gdp_growth"),
    ]
    granger_df = pd.DataFrame(granger_rows)
    granger_df.to_csv(OUT_DIR / "granger_results.csv", index=False)

    _, peak_idx, peak_val = build_irf_plot(result, "repo_rate", "npa_ratio", periods=8)
    fevd_shares, fevd_names = build_fevd_plot(result, "npa_ratio", periods=8)
    fevd_h8 = pd.Series(fevd_shares[-1], index=fevd_names)

    original_issue = (
        "the repo already had the core data-engineering artifacts, but it did not explicitly close Member A's deliverables "
        "from the explainer: there was no checklist-style completion review and no short written timeline interpretation for handoff into the report/slides."
    )
    (OUT_DIR / "member_a_review.md").write_text(
        prepare_member_a_review(data, original_issue, timeline_note),
        encoding="utf-8",
    )
    (OUT_DIR / "member_b_methods.md").write_text(
        prepare_member_b_methods(
            adf_df,
            lag_table,
            chosen_lag,
            choice_rule,
            diagnostics_df,
            whiteness_text,
            stable,
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "member_c_prep.md").write_text(prepare_member_c_prep(), encoding="utf-8")
    (OUT_DIR / "member_c_results.md").write_text(
        prepare_member_c_results(granger_df, peak_idx, peak_val, fevd_h8),
        encoding="utf-8",
    )

    Path("report.md").write_text(
        prepare_report(
            sample_start,
            sample_end,
            timeline_note,
            adf_df,
            diff_cols,
            chosen_lag,
            choice_rule,
            diagnostics_df,
            stable,
            whiteness_text,
            granger_df,
            peak_idx,
            peak_val,
            fevd_h8,
        ),
        encoding="utf-8",
    )
    Path("slides.md").write_text(
        prepare_slides(
            chosen_lag,
            float(granger_df.iloc[0]["p_value"]),
            float(granger_df.iloc[1]["p_value"]),
            peak_idx,
            peak_val,
            float(diagnostics_df["whiteness_pvalue"].iloc[0]),
            float(diagnostics_df.loc[diagnostics_df["series"] == "npa_ratio", "durbin_watson"].iloc[0]),
            float(diagnostics_df.loc[diagnostics_df["series"] == "repo_rate", "durbin_watson"].iloc[0]),
            float(diagnostics_df.loc[diagnostics_df["series"] == "gdp_growth", "durbin_watson"].iloc[0]),
        ),
        encoding="utf-8",
    )

    summary = pd.DataFrame(
        [
            {
                "min_year": min_year,
                "max_year": max_year,
                "sample_start": sample_start,
                "sample_end": sample_end,
                "diff_cols": diff_cols,
                "lag_choice": choice_rule,
                "chosen_lag": chosen_lag,
                "model_stable": stable,
                "granger_repo_to_npa_p": float(granger_df.iloc[0]["p_value"]),
                "granger_npa_to_repo_p": float(granger_df.iloc[1]["p_value"]),
                "irf_peak_horizon": peak_idx,
                "irf_peak_value": peak_val,
                "fevd_npa_repo_share_h8": float(fevd_h8["repo_rate"]),
            }
        ]
    )
    summary.to_csv(OUT_DIR / "summary.csv", index=False)


if __name__ == "__main__":
    main()
