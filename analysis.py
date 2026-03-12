import math
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


def load_npa_ratio() -> pd.DataFrame:
    df = pd.read_excel(DATA_DIR / "Dataset_1.xlsx", sheet_name=0, header=None)
    df = df[[1, 2, 5]].copy()
    df.columns = ["year", "bank", "npa_ratio"]
    df["bank"] = df["bank"].astype(str).str.strip().str.upper()
    df = df[df["bank"] == "ALL SCHEDULED COMMERCIAL BANKS"]
    df = df.dropna(subset=["year", "npa_ratio"])
    df["year"] = df["year"].astype(int)
    df = df.sort_values("year")
    return df[["year", "npa_ratio"]]


def load_wb_series(path: Path, value_name: str) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=4)
    df = df[df["Country Code"] == "IND"]
    year_cols = [c for c in df.columns if c.isdigit()]
    if df.empty or not year_cols:
        raise ValueError(f"No India data found in {path.name}")
    series = df[year_cols].iloc[0]
    out = series.reset_index()
    out.columns = ["year", value_name]
    out["year"] = out["year"].astype(int)
    out = out.dropna(subset=[value_name])
    return out


def annual_to_quarterly(
    df: pd.DataFrame,
    year_col: str,
    value_col: str,
    start_year: int,
    end_year: int,
) -> pd.Series:
    year_index = pd.PeriodIndex(df[year_col].astype(int), freq="Q-DEC")
    series = pd.Series(df[value_col].astype(float).values, index=year_index).sort_index()
    q_index = pd.period_range(f"{start_year}Q1", f"{end_year}Q4", freq="Q-DEC")
    series = series.reindex(q_index)
    series = series.interpolate(method="linear")
    return series


def adf_test(series: pd.Series) -> dict:
    result = adfuller(series.dropna(), autolag="AIC")
    return {
        "adf_stat": result[0],
        "p_value": result[1],
        "used_lag": result[2],
        "n_obs": result[3],
    }


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    npa = load_npa_ratio()
    repo = load_wb_series(
        DATA_DIR / "API_FR.INR.RINR_DS2_en_csv_v2_100.csv", "repo_rate"
    )
    gdp = load_wb_series(
        DATA_DIR / "API_NY.GDP.MKTP.KD.ZG_DS2_en_csv_v2_107.csv", "gdp_growth"
    )
    credit = load_wb_series(
        DATA_DIR / "API_FD.AST.PRVT.GD.ZS_DS2_en_csv_v2_1965.csv", "credit_growth"
    )

    series_meta = {
        "npa_ratio": npa,
        "repo_rate": repo,
        "gdp_growth": gdp,
        "credit_growth": credit,
    }

    min_year = max(df["year"].min() for df in series_meta.values())
    max_year = min(df["year"].max() for df in series_meta.values())
    min_year = max(min_year, 2005)
    max_year = min(max_year, 2023)
    if min_year > max_year:
        raise ValueError("No overlapping years in 2005-2023 range.")

    quarterly = {}
    for name, df in series_meta.items():
        quarterly[name] = annual_to_quarterly(df, "year", name, min_year, max_year)

    data = pd.DataFrame(quarterly)
    data.index.name = "quarter"
    data.to_csv(OUT_DIR / "cleaned_quarterly.csv")

    # Timeline plot
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))
    ts = data.copy()
    ts.index = ts.index.to_timestamp(how="end")
    ts.plot(ax=ax)
    ax.axvspan(pd.Timestamp("2015-01-01"), pd.Timestamp("2016-12-31"), color="grey", alpha=0.2)
    ax.set_title("Quarterly Series (Interpolated from Annual Data)")
    ax.set_ylabel("Value")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "timeline.png", dpi=150)
    plt.close(fig)

    # ADF tests
    adf_rows = []
    for col in data.columns:
        res = adf_test(data[col])
        res["series"] = col
        adf_rows.append(res)
    adf_df = pd.DataFrame(adf_rows)[
        ["series", "adf_stat", "p_value", "used_lag", "n_obs"]
    ].sort_values("series")
    adf_df.to_csv(OUT_DIR / "adf_results.csv", index=False)

    # Differencing based on ADF
    diff_cols = adf_df[adf_df["p_value"] > 0.05]["series"].tolist()
    data_var = data.copy()
    for col in diff_cols:
        data_var[col] = data_var[col].diff()
    data_var = data_var.dropna()
    data_var.to_csv(OUT_DIR / "cleaned_quarterly_differenced.csv")

    # VAR model
    model = VAR(data_var)
    order = model.select_order(8)
    selected = order.selected_orders
    p_aic = selected.get("aic")
    p_bic = selected.get("bic")
    if p_bic is None or (p_aic is not None and p_aic < p_bic):
        p = p_aic
        lag_choice = "AIC"
    else:
        p = p_bic
        lag_choice = "BIC"
    if p is None or p == 0:
        p = 1
        lag_choice = "Default"

    lag_df = pd.DataFrame(
        [
            {
                "lag_aic": p_aic,
                "lag_bic": p_bic,
                "chosen_lag": p,
                "choice_rule": lag_choice,
            }
        ]
    )
    lag_df.to_csv(OUT_DIR / "var_lag_order.csv", index=False)

    result = model.fit(p)

    # Diagnostics
    dw = durbin_watson(result.resid)
    diag_df = pd.DataFrame(
        {
            "series": data_var.columns,
            "durbin_watson": dw,
        }
    )
    diag_df.to_csv(OUT_DIR / "var_diagnostics.csv", index=False)

    # Granger causality tests
    def granger(caused: str, causing: str) -> dict:
        test = result.test_causality(caused=caused, causing=[causing], kind="f")
        return {
            "caused": caused,
            "causing": causing,
            "f_stat": float(test.test_statistic),
            "p_value": float(test.pvalue),
            "df_denom": getattr(test, "df_denom", np.nan),
            "df_num": getattr(test, "df_num", np.nan),
        }

    granger_rows = [
        granger("npa_ratio", "repo_rate"),
        granger("repo_rate", "npa_ratio"),
        granger("npa_ratio", "gdp_growth"),
        granger("npa_ratio", "credit_growth"),
    ]
    granger_df = pd.DataFrame(granger_rows)
    granger_df.to_csv(OUT_DIR / "granger_results.csv", index=False)

    # IRF: repo rate shock -> NPA response
    irf = result.irf(8)
    fig = irf.plot(impulse="repo_rate", response="npa_ratio")
    fig.suptitle("IRF: Repo Rate Shock -> NPA Ratio", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "irf_npa_repo.png", dpi=150)
    plt.close(fig)

    # FEVD for NPA
    fevd = result.fevd(8)
    idx_npa = list(data_var.columns).index("npa_ratio")
    steps = np.arange(1, fevd.decomp.shape[0])
    contrib = fevd.decomp[1:, idx_npa, :]
    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(steps))
    for i, col in enumerate(data_var.columns):
        ax.bar(steps, contrib[:, i], bottom=bottom, label=col)
        bottom += contrib[:, i]
    ax.set_title("FEVD for NPA Ratio")
    ax.set_xlabel("Horizon (quarters)")
    ax.set_ylabel("Variance share")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fevd_npa.png", dpi=150)
    plt.close(fig)

    # Summaries for report
    irf_values = irf.irfs[:, idx_npa, list(data_var.columns).index("repo_rate")]
    peak_idx = int(np.nanargmax(np.abs(irf_values)))
    peak_val = float(irf_values[peak_idx])
    fevd_h8 = contrib[-1]

    # Write report and slides
    report_path = Path("report.md")
    slides_path = Path("slides.md")

    report_lines = [
        "# RBI Rate Policy and Bank Stress: VAR Analysis",
        "",
        "## Data",
        f"- Quarterly series built from annual data (linear interpolation), covering {min_year}Q1 to {max_year}Q4.",
        "- NPA ratio: RBI Statistical Tables (Dataset_1.xlsx), All Scheduled Commercial Banks.",
        "- Repo rate proxy: World Bank real interest rate (FR.INR.RINR).",
        "- GDP growth: World Bank real GDP growth (NY.GDP.MKTP.KD.ZG).",
        "- Credit growth proxy: World Bank private credit to GDP (FD.AST.PRVT.GD.ZS).",
        "",
        "## Methods",
        "- ADF tests run per series; non-stationary series differenced once.",
        f"- VAR lag order selected by {lag_choice}; chosen lag = {p}.",
        "- Granger causality tests run for NPA vs repo rate and controls.",
        "- IRF computed for a repo-rate shock; FEVD computed for NPA.",
        "",
        "## Results",
        f"- ADF p-values: {', '.join([f'{r.series}={r.p_value:.3f}' for r in adf_df.itertuples()])}",
        f"- Differenced series: {', '.join(diff_cols) if diff_cols else 'None'}",
        f"- Granger repo -> NPA p-value: {granger_df.iloc[0]['p_value']:.4f}",
        f"- Granger NPA -> repo p-value: {granger_df.iloc[1]['p_value']:.4f}",
        f"- IRF peak |response| at horizon {peak_idx} quarters: {peak_val:.4f}",
        f"- FEVD at 8 quarters (NPA variance share): "
        + ", ".join(
            [f"{col}={fevd_h8[i]:.2f}" for i, col in enumerate(data_var.columns)]
        ),
        "",
        "## Limitations",
        "- Annual World Bank data interpolated to quarterly frequency; results should be treated as indicative.",
        "- Repo rate proxy uses real interest rate due to data availability in provided files.",
        "",
        "## Outputs",
        "- outputs/cleaned_quarterly.csv",
        "- outputs/cleaned_quarterly_differenced.csv",
        "- outputs/timeline.png",
        "- outputs/irf_npa_repo.png",
        "- outputs/fevd_npa.png",
        "- outputs/adf_results.csv",
        "- outputs/granger_results.csv",
        "- outputs/var_lag_order.csv",
    ]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    slides_lines = [
        "# Slide Outline (10-12 slides)",
        "",
        "1. Title: RBI Rate Policy vs Bank Stress (Question + team).",
        "2. Motivation: 2013-2018 NPA spike + RBI rate changes.",
        "3. Data: four series, sources, period, interpolation note.",
        "4. ADF test results and differencing decision.",
        "5. VAR model setup and chosen lag order.",
        "6. VAR stability/diagnostics (Durbin-Watson summary).",
        "7. Granger causality results (repo -> NPA, NPA -> repo).",
        "8. IRF plot: repo shock -> NPA response.",
        "9. FEVD plot: NPA variance shares.",
        "10. Answer to main question (directional evidence).",
        "11. Limitations and robustness notes.",
        "12. Conclusion + policy interpretation.",
        "",
        "Plots to include:",
        "- outputs/timeline.png",
        "- outputs/irf_npa_repo.png",
        "- outputs/fevd_npa.png",
    ]
    slides_path.write_text("\n".join(slides_lines), encoding="utf-8")

    summary = {
        "min_year": min_year,
        "max_year": max_year,
        "diff_cols": diff_cols,
        "lag_choice": lag_choice,
        "chosen_lag": p,
        "granger_repo_to_npa_p": float(granger_df.iloc[0]["p_value"]),
        "granger_npa_to_repo_p": float(granger_df.iloc[1]["p_value"]),
        "irf_peak_horizon": peak_idx,
        "irf_peak_value": peak_val,
    }
    pd.DataFrame([summary]).to_csv(OUT_DIR / "summary.csv", index=False)


if __name__ == "__main__":
    main()
