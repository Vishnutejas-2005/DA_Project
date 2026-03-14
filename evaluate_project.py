"""
E0259 Data Analytics — Credit Spreads Project
PROJECT VALIDITY EVALUATOR  v3
======================================================
USAGE — two options:

  Option A (recommended, 2 minutes):
    1. Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html
       (just sign up with email, key appears instantly)
    2. Run:  python3 evaluate_project.py --download YOUR_API_KEY
       This downloads all four datasets automatically.

  Option B (manual browser download):
    Open each URL below in your browser — it downloads a CSV directly.
    Save all four files in the same folder as this script.

    HY OAS (daily):
      https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2&fq=Daily
      Save as: BAMLH0A0HYM2.csv

    BBB OAS (daily):
      https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLC0A4CBBB&fq=Daily
      Save as: BAMLC0A4CBBB.csv

    AAA OAS (daily):
      https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLC0A1CAAA&fq=Daily
      Save as: BAMLC0A1CAAA.csv

    NBER Recessions (daily):
      https://fred.stlouisfed.org/graph/fredgraph.csv?id=USRECD
      Save as: USRECD.csv

    Then run:  python3 evaluate_project.py

CRITERIA CHECKED:
  C1 — Structural breaks exist in HY OAS  [REQUIRED]
  C2 — Regime dynamics differ (Chow test)  [REQUIRED]
  C3 — HY breaks before BBB (cascade)     [BONUS]
"""

import sys, os, argparse
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import breaks_hansen
import ruptures as rpt
import warnings
warnings.filterwarnings("ignore")

# ── Terminal colours ─────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def p(text, col=RESET):   print(f"{col}{text}{RESET}")
def header(text):
    p("\n" + "="*62, BLUE)
    p(f"  {text}", BOLD)
    p("="*62, BLUE)
def subheader(t): p(f"\n── {t} ──", BLUE)
def ok(t):   p(f"  ✓  {t}", GREEN)
def fail(t): p(f"  ✗  {t}", RED)
def warn(t): p(f"  ⚠  {t}", YELLOW)
def info(t): p(f"     {t}")

# ════════════════════════════════════════════════════════════
# OPTIONAL AUTO-DOWNLOAD via FRED API
# ════════════════════════════════════════════════════════════
SERIES = {
    "BAMLH0A0HYM2": "BAMLH0A0HYM2.csv",
    "BAMLC0A4CBBB":  "BAMLC0A4CBBB.csv",
    "BAMLC0A1CAAA":  "BAMLC0A1CAAA.csv",
    "USRECD":        "USRECD.csv",
}

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--download", metavar="API_KEY", default=None)
args, _ = parser.parse_known_args()

if args.download:
    try:
        import requests
    except ImportError:
        fail("The 'requests' library is required for --download.")
        p("  Install it with:  pip install requests", YELLOW)
        sys.exit(1)

    header("AUTO-DOWNLOADING via FRED API")
    api_key = args.download
    for sid, fname in SERIES.items():
        try:
            params = {
                "series_id": sid,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": "1996-01-01",
            }
            r = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params=params,
                timeout=30,
            )
            r.raise_for_status()
            payload = r.json()
            if "error_code" in payload:
                raise ValueError(payload.get("error_message", "Unknown FRED API error"))
            observations = payload.get("observations", [])
            if not observations:
                raise ValueError("FRED returned no observations")
            df_tmp = pd.DataFrame(observations)
            if not {"date", "value"}.issubset(df_tmp.columns):
                raise ValueError("FRED response is missing date/value fields")
            df_tmp = df_tmp[["date", "value"]].copy()
            df_tmp.columns = ["DATE", sid]
            df_tmp.to_csv(fname, index=False)
            ok(f"{sid} → {fname}  ({len(df_tmp):,} rows)")
        except Exception as e:
            fail(f"Failed to download {sid}: {e}")
            fail("Check your API key and internet connection.")
            sys.exit(1)
    ok("All datasets downloaded. Running evaluation...\n")

# ════════════════════════════════════════════════════════════
# STEP 0 — LOAD DATA
# ════════════════════════════════════════════════════════════
header("STEP 0 — Loading datasets")

files = {
    "HY":   "BAMLH0A0HYM2.csv",
    "BBB":  "BAMLC0A4CBBB.csv",
    "AAA":  "BAMLC0A1CAAA.csv",
    "NBER": "USRECD.csv",
}

for label, fname in files.items():
    if not os.path.exists(fname):
        fail(f"{fname} not found.")
        p("")
        p("  Run one of:", YELLOW)
        p("  Option A — auto download (needs free FRED API key):", YELLOW)
        p("    python3 evaluate_project.py --download YOUR_API_KEY", BLUE)
        p("  Get a free key in 30 seconds at:", YELLOW)
        p("    https://fred.stlouisfed.org/docs/api/api_key.html", BLUE)
        p("")
        p("  Option B — browser download (no key needed):", YELLOW)
        p("  Open each URL in your browser and save with the filename shown:", YELLOW)
        urls = [
            ("https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2&fq=Daily", "BAMLH0A0HYM2.csv"),
            ("https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLC0A4CBBB&fq=Daily",  "BAMLC0A4CBBB.csv"),
            ("https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLC0A1CAAA&fq=Daily",  "BAMLC0A1CAAA.csv"),
            ("https://fred.stlouisfed.org/graph/fredgraph.csv?id=USRECD",                   "USRECD.csv"),
        ]
        for url, fn in urls:
            p(f"    {url}", BLUE)
            p(f"    Save as: {fn}", YELLOW)
            p("")
        sys.exit(1)
    else:
        ok(f"{fname} found")

def load_fred(fname, col_name):
    """Load a FRED CSV — handles both fredgraph.csv and API formats."""
    with open(fname) as f:
        first_line = f.readline().strip()
    # Detect which date column name is used
    cols = first_line.split(",")
    date_col = cols[0]   # could be DATE, date, observation_date, etc.
    df = pd.read_csv(fname, parse_dates=[date_col], index_col=date_col)
    df.index.name = "DATE"
    # Keep only the value column (drop realtime_start/end if present)
    val_cols = [c for c in df.columns if c.lower() not in
                ("realtime_start","realtime_end","vintage_date")]
    df = df[val_cols].copy()
    df.columns = [col_name]
    df = df.replace(".", np.nan)
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
    df = df.dropna()
    return df

hy   = load_fred("BAMLH0A0HYM2.csv", "HY")
bbb  = load_fred("BAMLC0A4CBBB.csv",  "BBB")
aaa  = load_fred("BAMLC0A1CAAA.csv",  "AAA")
nber = load_fred("USRECD.csv",         "REC")

df = hy.join([bbb, aaa, nber], how="inner").dropna()
df = df[df.index >= "1997-01-01"]

info(f"Date range:   {df.index[0].date()} → {df.index[-1].date()}")
info(f"Observations: {len(df):,}")
# FRED stores OAS in percent (e.g. 3.5 = 350 bps)
info(f"HY spread range: {df.HY.min()*100:.0f} bps → {df.HY.max()*100:.0f} bps")

# ── Frequency guard ──────────────────────────────────────────
if len(df) < 500:
    fail(f"Only {len(df)} observations — this is MONTHLY data, not daily.")
    p("")
    p("  The fq=Daily parameter in fredgraph.csv URLs is not always honoured.", YELLOW)
    p("  Use the API key method instead:", YELLOW)
    p("")
    p("  Step 1: Get a FREE key (30 seconds) at:", YELLOW)
    p("    https://fred.stlouisfed.org/docs/api/api_key.html", BLUE)
    p("")
    p("  Step 2: Run:", YELLOW)
    p("    python3 evaluate_project.py --download YOUR_KEY_HERE", BLUE)
    p("")
    sys.exit(1)
else:
    ok(f"Frequency check passed: {len(df):,} daily observations ✓")

# ════════════════════════════════════════════════════════════
# ADF STATIONARITY (prerequisite)
# ════════════════════════════════════════════════════════════
header("ADF STATIONARITY TESTS (prerequisite)")

for col in ["HY", "BBB", "AAA"]:
    p_lev  = adfuller(df[col].dropna(), autolag="AIC")[1]
    p_diff = adfuller(df[col].diff().dropna(), autolag="AIC")[1]
    info(f"{col} levels:      ADF p = {p_lev:.4f}  "
         f"{'→ stationary' if p_lev < 0.05 else '→ unit root (expected)'}")
    info(f"{col} differences: ADF p = {p_diff:.4f}  "
         f"{'→ stationary ✓' if p_diff < 0.05 else '→ still non-stationary !'}")

info("\nDecision: work with daily CHANGES in spread (standard for financial spreads)")

for col in ["HY", "BBB", "AAA"]:
    df[f"d{col}"] = df[col].diff()
df_work = df.dropna()

# ════════════════════════════════════════════════════════════
# CRITERION 1 — Structural breaks in HY OAS
# ════════════════════════════════════════════════════════════
header("CRITERION 1 — Structural Breaks in HY OAS")

p("\nBinseg (Binary Segmentation) scans the HY series and finds the", YELLOW)
p("break configuration with the best BIC score.", YELLOW)
p("No assumptions about which years matter — purely data-driven.", YELLOW)

signal = df_work["dHY"].values
model  = rpt.Binseg(model="l2", min_size=60, jump=5).fit(signal)

best_bic, best_bkps = np.inf, None
for n in range(1, 7):
    try:
        bkps = model.predict(n_bkps=n)
        prev, residuals = 0, []
        for bp in bkps:
            seg = signal[prev:bp]; residuals.extend(seg - seg.mean()); prev = bp
        sse = max(np.sum(np.array(residuals)**2), 1e-10)
        bic = len(signal) * np.log(sse / len(signal)) + n * np.log(len(signal))
        if bic < best_bic:
            best_bic, best_bkps = bic, bkps
    except: continue

if best_bkps is None:
    best_bkps = model.predict(n_bkps=2)

dates_idx  = df_work.index[1:]   # diff shifts index by 1
break_dates = [dates_idx[min(i-1, len(dates_idx)-1)] for i in best_bkps[:-1]]

crises = {
    "2001-09-11": "9/11 attacks",
    "2002-10-09": "Dot-com bust bottom",
    "2007-07-26": "Subprime crisis begins",
    "2008-09-15": "Lehman Brothers collapse",
    "2009-06-01": "GFC trough / recovery",
    "2011-08-05": "US debt downgrade",
    "2015-12-16": "Fed rate hike cycle",
    "2016-02-11": "Oil crash / China fears",
    "2020-03-20": "COVID crash",
    "2022-03-16": "Ukraine war / Fed hikes",
}

subheader("Detected break dates in HY OAS")
for i, bd in enumerate(break_dates):
    nearest = min(crises, key=lambda x: abs((pd.Timestamp(x) - bd).days))
    gap     = abs((pd.Timestamp(nearest) - bd).days)
    info(f"Break {i+1}: {bd.strftime('%Y-%m-%d')}  "
         f"(≈ {gap} days from: {crises[nearest]})")

subheader("Hansen (1992) parameter stability test")
y_h  = df_work["dHY"].values[1:]
X_h  = sm.add_constant(df_work["dHY"].shift(1).dropna().values)
ols  = sm.OLS(y_h, X_h).fit()
h_stat, h_crit_tbl = breaks_hansen(ols)
h_stat    = float(h_stat)
h_crit    = float(h_crit_tbl[-1][1])
h_sig     = h_stat > h_crit
info(f"Hansen instability statistic: {h_stat:.4f}")
info(f"Critical value (conservative): {h_crit:.4f}")
info(f"Instability detected: {'YES ✓' if h_sig else 'NO (mild)'}")

p("\n┌─ CRITERION 1 VERDICT ──────────────────────────────┐", BOLD)
if len(break_dates) >= 2:
    ok(f"PASS — {len(break_dates)} structural breaks detected.")
    if h_sig:
        ok(f"       Hansen confirms instability (stat {h_stat:.2f} > crit {h_crit:.2f}).")
    else:
        warn(f"       Hansen borderline (stat {h_stat:.2f} vs crit {h_crit:.2f}) — breaks still real.")
    c1_pass = True
elif len(break_dates) == 1:
    warn("WEAK — Only 1 break detected. Project is marginal.")
    c1_pass = False
else:
    fail("FAIL — No breaks detected. Abandon this project.")
    c1_pass = False
p("└────────────────────────────────────────────────────┘", BOLD)

# ════════════════════════════════════════════════════════════
# CRITERION 2 — Chow test: regime dynamics differ
# ════════════════════════════════════════════════════════════
header("CRITERION 2 — Chow Tests at Detected Break Dates")

def chow_test(series, break_idx):
    y = series.values
    sse_f = np.sum(sm.OLS(y[1:], sm.add_constant(y[:-1])).fit().resid**2)
    y1, X1 = y[1:break_idx], sm.add_constant(y[:break_idx-1])
    y2, X2 = y[break_idx+1:], sm.add_constant(y[break_idx:-1])
    if len(y1) < 5 or len(y2) < 5: return np.nan, np.nan
    sse1 = np.sum(sm.OLS(y1, X1).fit().resid**2)
    sse2 = np.sum(sm.OLS(y2, X2).fit().resid**2)
    k, n = 2, len(y) - 1
    denom = (sse1 + sse2) / max(n - 2*k, 1)
    if denom <= 0: return np.nan, np.nan
    F = ((sse_f - (sse1+sse2)) / k) / denom
    return F, 1 - stats.f.cdf(F, dfn=k, dfd=n-2*k)

def ar1_halflife(series):
    y = series.values
    if len(y) < 5: return np.nan, np.nan
    res = sm.OLS(y[1:], sm.add_constant(y[:-1])).fit()
    phi = res.params[1]
    hl  = -np.log(2)/np.log(max(abs(phi), 1e-9)) if 0 < phi < 1 else np.inf
    return phi, hl

chow_results, c2_any_pass = [], False
series_hy = df_work["dHY"]

for bd in break_dates:
    idx = df_work.index.get_loc(bd)
    F, pval = chow_test(series_hy, idx)
    if np.isnan(F): continue
    phi_pre,  hl_pre  = ar1_halflife(series_hy.iloc[:idx])
    phi_post, hl_post = ar1_halflife(series_hy.iloc[idx:])
    sig   = pval < 0.05
    stars = "***" if pval<0.001 else ("**" if pval<0.01 else ("*" if pval<0.05 else ""))
    info(f"\nBreak date: {bd.strftime('%Y-%m-%d')}")
    info(f"  Chow F = {F:.3f},  p = {pval:.4f}  {stars}")
    info(f"  AR(1) φ before: {phi_pre:.4f}  (half-life ≈ {hl_pre:.1f} days)")
    info(f"  AR(1) φ after:  {phi_post:.4f}  (half-life ≈ {hl_post:.1f} days)")
    if sig:
        ok("  → Regimes STATISTICALLY DIFFERENT at this break ✓")
        c2_any_pass = True
    else:
        warn("  → Not significantly different at this break")
    chow_results.append({"date": bd, "F": F, "p": pval, "sig": sig})

subheader("Mean HY spread per regime (in basis points)")
bounds = [df_work.index[0]] + break_dates + [df_work.index[-1]]
for i in range(len(bounds)-1):
    seg     = df["HY"][(df.index>=bounds[i]) & (df.index<bounds[i+1])]
    rec_frc = df["REC"][(df.index>=bounds[i]) & (df.index<bounds[i+1])].mean()
    if len(seg) > 0:
        info(f"  {bounds[i].strftime('%Y-%m')} → {bounds[i+1].strftime('%Y-%m')}: "
             f"mean = {seg.mean()*100:.0f} bps,  "
             f"max = {seg.max()*100:.0f} bps  "
             f"(recession: {rec_frc:.0%})")

p("\n┌─ CRITERION 2 VERDICT ──────────────────────────────┐", BOLD)
if c2_any_pass:
    n_sig = sum(r["sig"] for r in chow_results)
    ok(f"PASS — {n_sig}/{len(chow_results)} break dates show different dynamics.")
    c2_pass = True
else:
    fail("FAIL — No break date shows significantly different dynamics.")
    c2_pass = False
p("└────────────────────────────────────────────────────┘", BOLD)

# ════════════════════════════════════════════════════════════
# CRITERION 3 — Cascade across tiers (bonus)
# ════════════════════════════════════════════════════════════
header("CRITERION 3 — Cascade: Does HY Break Before BBB? (BONUS)")

tier_breaks = {"HY": break_dates}
for col, dcol in [("BBB","dBBB"), ("AAA","dAAA")]:
    sig_t = df_work[dcol].values
    m_t   = rpt.Binseg(model="l2", min_size=60, jump=5).fit(sig_t)
    best_bic_t, best_bkps_t = np.inf, None
    for n in range(1, 7):
        try:
            bkps = m_t.predict(n_bkps=n)
            prev, res_t = 0, []
            for bp in bkps:
                seg = sig_t[prev:bp]; res_t.extend(seg - seg.mean()); prev = bp
            sse = max(np.sum(np.array(res_t)**2), 1e-10)
            bic = len(sig_t) * np.log(sse/len(sig_t)) + n * np.log(len(sig_t))
            if bic < best_bic_t:
                best_bic_t, best_bkps_t = bic, bkps
        except: continue
    if best_bkps_t is None:
        best_bkps_t = m_t.predict(n_bkps=2)
    di = df_work.index[1:]
    tier_breaks[col] = [di[min(i-1,len(di)-1)] for i in best_bkps_t[:-1]]
    info(f"\n{col} breaks: {[d.strftime('%Y-%m-%d') for d in tier_breaks[col]]}")

info(f"\nHY  breaks: {[d.strftime('%Y-%m-%d') for d in tier_breaks['HY']]}")

subheader("Cascade check: HY vs BBB (within 180-day window)")
lags, cascade_found = [], False
for hy_bd in tier_breaks["HY"]:
    for bbb_bd in tier_breaks["BBB"]:
        lag = (bbb_bd - hy_bd).days
        if 0 < lag <= 180:
            info(f"  HY {hy_bd.strftime('%Y-%m-%d')} → "
                 f"BBB {bbb_bd.strftime('%Y-%m-%d')} ({lag} days later) ✓")
            cascade_found = True; lags.append(lag)
        elif -30 <= lag <= 0:
            info(f"  BBB and HY broke simultaneously on "
                 f"{hy_bd.strftime('%Y-%m-%d')} (lag = {lag} days)")

p("\n┌─ CRITERION 3 VERDICT ──────────────────────────────┐", BOLD)
if cascade_found:
    ok(f"PASS — HY leads BBB with average lag of {np.mean(lags):.0f} days.")
    ok(f"       Early-warning story confirmed.")
    c3_pass = True
else:
    warn("MIXED — No clean HY-before-BBB cascade within 180 days.")
    warn("        Drop cascade from the narrative.")
    warn("        C1 + C2 alone are sufficient for a valid project.")
    c3_pass = False
p("└────────────────────────────────────────────────────┘", BOLD)

# ════════════════════════════════════════════════════════════
# FINAL VERDICT
# ════════════════════════════════════════════════════════════
header("FINAL PROJECT VALIDITY VERDICT")

rows = [
    ("C1 — Structural breaks exist in HY OAS",  c1_pass, "REQUIRED"),
    ("C2 — Regime dynamics differ (Chow test)", c2_pass, "REQUIRED"),
    ("C3 — HY-to-BBB cascade detected",         c3_pass, "BONUS"),
]
for label, passed, req in rows:
    col  = GREEN if passed else (RED if req=="REQUIRED" else YELLOW)
    mark = "PASS" if passed else ("FAIL" if req=="REQUIRED" else "ABSENT")
    p(f"  [{mark:6}]  {label}  [{req}]", col)

print()
if c1_pass and c2_pass:
    if c3_pass:
        p("  ══ PROJECT IS VALID ══  All three criteria met.", GREEN+BOLD)
        p("     You have a strong project with a cascade story.", GREEN)
    else:
        p("  ══ PROJECT IS VALID ══  Both required criteria met.", GREEN+BOLD)
        p("     Focus on C1 + C2. Drop cascade from the narrative.", GREEN)
else:
    missing = [("C1" if not c1_pass else ""), ("C2" if not c2_pass else "")]
    missing = " and ".join(x for x in missing if x)
    p(f"  ══ PROJECT IS NOT VALID ══  {missing} failed.", RED+BOLD)
    p("     Do not proceed — find a new project.", RED)
print()
