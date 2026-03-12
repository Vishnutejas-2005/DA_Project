# RBI Rate Policy and Bank Stress: VAR Analysis

## Data
- Quarterly series built from annual data (linear interpolation), covering 2005Q1 to 2021Q4.
- NPA ratio: RBI Statistical Tables (Dataset_1.xlsx), All Scheduled Commercial Banks.
- Repo rate proxy: World Bank real interest rate (FR.INR.RINR).
- GDP growth: World Bank real GDP growth (NY.GDP.MKTP.KD.ZG).
- Credit growth proxy: World Bank private credit to GDP (FD.AST.PRVT.GD.ZS).

## Methods
- ADF tests run per series; non-stationary series differenced once.
- VAR lag order selected by BIC; chosen lag = 1.
- Granger causality tests run for NPA vs repo rate and controls.
- IRF computed for a repo-rate shock; FEVD computed for NPA.

## Results
- ADF p-values: credit_growth=0.054, gdp_growth=0.165, npa_ratio=0.472, repo_rate=0.152
- Differenced series: credit_growth, gdp_growth, npa_ratio, repo_rate
- Granger repo -> NPA p-value: 0.9541
- Granger NPA -> repo p-value: 0.2793
- IRF peak |response| at horizon 8 quarters: -0.0170
- FEVD at 8 quarters (NPA variance share): npa_ratio=0.00, repo_rate=0.08, gdp_growth=0.75, credit_growth=0.17

## Limitations
- Annual World Bank data interpolated to quarterly frequency; results should be treated as indicative.
- Repo rate proxy uses real interest rate due to data availability in provided files.

## Outputs
- outputs/cleaned_quarterly.csv
- outputs/cleaned_quarterly_differenced.csv
- outputs/timeline.png
- outputs/irf_npa_repo.png
- outputs/fevd_npa.png
- outputs/adf_results.csv
- outputs/granger_results.csv
- outputs/var_lag_order.csv