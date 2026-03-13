# RBI Rate Policy and Bank Stress: VAR Analysis

## Data
We construct a quarterly panel from 2005Q1 to 2021Q4 using four series for India. The Gross NPA ratio comes from RBI Statistical Tables for All Scheduled Commercial Banks. The remaining three series come from the provided World Bank files: real interest rate as the repo-rate proxy, real GDP growth, and private-sector credit to GDP as the credit-growth proxy. Because the World Bank files are annual, they are linearly interpolated to quarterly frequency to match the project brief.

The timeline shows a pronounced banking-stress cycle: the interpolated Gross NPA ratio rises from 3.23% in 2013Q1 to a local peak of 11.18% in 2018Q1. The repo-rate proxy is highest in 2015Q1 and remains elevated through the 2015-16 policy-tightening window (about 7.56% in 2015Q1 and 5.55% in 2016Q4). GDP growth and credit growth weaken around the same period, so the visual story is consistent with a broad macro-financial stress episode rather than a clean one-variable shock.

## Methods
We ran Augmented Dickey-Fuller tests on each series and treated p-values below 0.05 as evidence of stationarity. The ADF results were: credit_growth: p=0.054, gdp_growth: p=0.165, npa_ratio: p=0.472, repo_rate: p=0.152. The series differenced once before estimation were: credit_growth, gdp_growth, npa_ratio, repo_rate. We then estimated a VAR with lag order 1, selected by BIC from the information criteria table. Diagnostics show Durbin-Watson values of npa_ratio=1.87, repo_rate=1.77, gdp_growth=1.74, credit_growth=1.75; the system is stable = True; whiteness check: Portmanteau stat = 72.8258, p = 0.2104.

## Results
The main Granger result is weak in both directions. For repo-rate history predicting NPA movements, the test yields F = 0.0033 and p = 0.9541. For NPA history predicting the repo-rate proxy, the test yields F = 1.1758 and p = 0.2793. The impulse-response function shows a peak absolute NPA response of -0.0170 after 8 quarters following a one-unit repo-rate shock. At the 8-quarter horizon, the FEVD for NPA variance is npa_ratio=0.93, repo_rate=0.02, gdp_growth=0.01, credit_growth=0.05.

## Conclusion
On the provided dataset, we do not find statistically significant evidence that the repo-rate proxy Granger-causes the NPA ratio, nor that the NPA ratio Granger-causes the repo-rate proxy, at the 5% level. The estimated dynamics are economically modest, and the decomposition suggests that NPA's own momentum dominates while the rate proxy contributes only a small share in this setup. The correct takeaway for the presentation is therefore cautious: the data support correlation within a broader stress episode, but not a strong directional causality claim.

## Limitations
- The World Bank macro series are annual and have been interpolated to quarterly frequency.
- The project files do not contain the literal RBI repo-rate series, so the real interest rate is used as a proxy.
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