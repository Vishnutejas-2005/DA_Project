# Member B Deliverable

## Stationarity (ADF)
- credit_growth: p = 0.0539, stationary at 5% = False
- gdp_growth: p = 0.1650, stationary at 5% = False
- npa_ratio: p = 0.4716, stationary at 5% = False
- repo_rate: p = 0.1517, stationary at 5% = False

## Lag Selection
- Chosen lag order = 1 using BIC.
- Full information-criterion table is saved in `outputs/var_lag_order.csv`.

## Diagnostics
- VAR stable = True. Stability plot saved to `outputs/var_stability.png`.
- npa_ratio: Durbin-Watson = 1.867
- repo_rate: Durbin-Watson = 1.767
- gdp_growth: Durbin-Watson = 1.739
- credit_growth: Durbin-Watson = 1.750
- Residual whiteness check: Portmanteau stat = 72.8258, p = 0.2104

## Methods Paragraph
We first ran Augmented Dickey-Fuller tests on each quarterly series to check whether the levels were stationary. Any series with p-value above 0.05 was differenced once before entering the VAR. We then selected the VAR lag order using standard information criteria from statsmodels, prioritising BIC for parsimony given the short quarterly sample. After fitting the model, we checked that the system was stable and that residual autocorrelation was not obviously severe.