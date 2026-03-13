# Member B Deliverable

## Stationarity (ADF)
- gdp_growth: p = 0.1863, stationary at 5% = False
- npa_ratio: p = 0.3511, stationary at 5% = False
- repo_rate: p = 0.1190, stationary at 5% = False

## Lag Selection
- Chosen lag order = 1 using BIC.
- Full information-criterion table is saved in `outputs/var_lag_order.csv`.

## Diagnostics
- VAR stable = True. Stability plot saved to `outputs/var_stability.png`.
- npa_ratio: Durbin-Watson = 1.866
- repo_rate: Durbin-Watson = 1.752
- gdp_growth: Durbin-Watson = 1.739
- Residual whiteness check: Portmanteau stat = 70.4660, p = 0.0005
- Interpretation: The Portmanteau whiteness test rejects residual whiteness at the 5% level, so the fitted VAR should be presented as informative but not fully clean on residual autocorrelation.

## Methods Paragraph
We first ran Augmented Dickey-Fuller tests on each quarterly series to check whether the levels were stationary. Any series with p-value above 0.05 was differenced once before entering the VAR. We then selected the VAR lag order using standard information criteria from statsmodels, prioritising BIC for parsimony given the short quarterly sample. After fitting the 3-variable VAR, we checked that the system was stable and then inspected residual autocorrelation. Because the macro series are annual and linearly interpolated to quarterly frequency, these ADF outcomes should be presented as indicative rather than as clean high-frequency stationarity evidence.