# RBI Rate Policy and Bank Stress: VAR Analysis

## Data
We construct a quarterly panel from 2005Q4 to 2022Q1 using three series for India. The Gross NPA ratio comes from RBI Statistical Tables for All Scheduled Commercial Banks. The two macro-financial controls come from the provided World Bank files: real interest rate as the repo-rate proxy and real GDP growth as the output control. Because the World Bank files are annual, they are linearly interpolated to quarterly frequency to match the project brief. We drop the original credit-growth control from the final VAR because the provided World Bank credit series for India ends in 2021 and would otherwise shorten the sample materially.

The timeline shows a pronounced banking-stress cycle: the interpolated Gross NPA ratio rises from 3.23% in 2013Q1 to a local peak of 11.18% in 2018Q1. The repo-rate proxy is highest in 2015Q1 and remains elevated through the 2015-16 policy-tightening window (about 7.56% in 2015Q1 and 5.55% in 2016Q4). GDP growth also softens around the same period, so the visual story is consistent with a broad macro-financial stress episode rather than a clean one-variable shock.

## Methods
We ran Augmented Dickey-Fuller tests on each series and treated p-values below 0.05 as evidence of stationarity. The ADF results were: gdp_growth: p=0.304, npa_ratio: p=0.305, repo_rate: p=0.139. The series differenced once before estimation were: gdp_growth, npa_ratio, repo_rate. We then estimated a 3-variable VAR with lag order 1, selected by BIC from the information criteria table. Note that AIC selected lag=5 while BIC selected lag=1; given the short interpolated sample this gap is expected and BIC is preferred for parsimony. Diagnostics show Durbin-Watson values of npa_ratio=1.85, repo_rate=1.63, gdp_growth=1.74; the system is stable = True; whiteness check: Portmanteau stat = 57.8661, p = 0.0119.

## Diagnostics
The Portmanteau test rejects residual whiteness (p = 0.0119), which is common in short interpolated quarterly panels and likely reflects the mechanical smoothness introduced by annual-to-quarterly interpolation rather than a structural model misspecification. The VAR is stable and the Durbin-Watson values are close to 2.0 across all equations, so the results are treated as indicative.
More specifically, linear annual-to-quarterly interpolation creates repeated intra-year step sizes, so after differencing several adjacent quarterly observations can be mechanically very similar rather than genuinely independent. That means the exact Granger and Portmanteau p-values should be interpreted cautiously even though the overall non-significant direction-of-causality result is still informative.

## Results
The main Granger result is negative in both directions. For repo-rate history predicting NPA movements, the test yields F = 0.3626 and p = 0.5478, which is essentially no predictive power in this specification. For NPA history predicting the repo-rate proxy, the test yields F = 0.0104 and p = 0.9187. The impulse-response function shows a peak absolute NPA response of 0.0381 after 4 quarters following a one-unit repo-rate shock. At the 8-quarter horizon, the FEVD for NPA variance is npa_ratio=0.97, repo_rate=0.02, gdp_growth=0.00.

## Conclusion
On the provided dataset, we do not find statistically significant evidence that the repo-rate proxy Granger-causes the NPA ratio, nor that the NPA ratio Granger-causes the repo-rate proxy, at the 5% level. The estimated dynamics are economically modest, and the decomposition suggests that NPA's own momentum dominates while the rate proxy and GDP control contribute only small shares in this setup. Given the proxy rate, interpolated macro series, and the diagnostic caveat above, these results are best interpreted as exploratory evidence rather than a structural causal estimate. The core finding, that neither direction of causality is significant in this specification, is robust to the lag selection and stable across the 3-variable setup.

## Limitations
- The World Bank macro series are annual and have been interpolated to quarterly frequency.
- The interpolation step also creates boundary artifacts: 2005Q1-Q3 would be mechanically backfilled from the 2005 anchor and 2022Q2-Q4 would be forward-filled from the 2022 NPA anchor, so the panel is trimmed to 2005Q4-2022Q1 to exclude those fabricated edge quarters.
- Linear interpolation can create repeated within-year changes after differencing, so the effective number of independent quarterly movements is lower than the raw row count suggests.
- The original credit-growth control was dropped because the provided World Bank credit series for India ends in 2021.
- The project files do not contain the literal RBI repo-rate series, so the real interest rate is used as a proxy.
- RBI NPA values are reported at the March fiscal year-end; we align them to calendar Q1 of the named year, while the World Bank annual series remain a coarse calendar-year proxy.
- GDP growth (World Bank NY.GDP.MKTP.KD.ZG) is already a percentage-change series; the ADF test classified it as non-stationary so it was differenced once, meaning the VAR uses the quarter-on-quarter change in GDP growth (acceleration), not the growth rate itself.
- Results should be presented as indicative rather than as a definitive structural causal estimate.

## Outputs
- outputs/cleaned_quarterly.csv
- outputs/cleaned_quarterly_differenced.csv
- outputs/timeline.png
- outputs/var_stability.png
- outputs/irf_npa_repo.png
- outputs/fevd_npa.png
- outputs/adf_results.csv
- outputs/granger_results.csv
- outputs/var_lag_order.csv
- outputs/var_diagnostics.csv