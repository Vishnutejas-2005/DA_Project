# Slide Outline (12 slides)

1. Title
Question: Does RBI rate policy cause bank stress, or does bank stress cause the RBI to act?

2. Why this matters
2013-2018 NPA spike, macro stress, and possible policy feedback.

3. Data
Three series, 2005Q1-2022Q4, RBI + World Bank, annual macro data interpolated to quarterly frequency. Explain that the credit-growth control was dropped because its source coverage ended in 2021.

4. Timeline plot
Use `outputs/timeline.png`; highlight the 2015-16 tightening window.

5. Stationarity results
Use `outputs/adf_results.csv`; explain which series were differenced and note that annual-to-quarterly interpolation can create overly smooth stationarity patterns.

6. VAR setup
Lag order = 2; explain why BIC/AIC was used and that the final model is a 3-variable VAR.

7. Diagnostics and stability
VAR is stable (all inverse roots inside unit circle). Durbin-Watson ~= 2 across equations - no severe autocorrelation. Portmanteau test flags residual correlation (p = 0.003), likely from annual->quarterly interpolation smoothness. Model is treated as indicative, not structural.

8. Granger causality
Repo -> NPA p-value = 0.6815; NPA -> Repo p-value = 0.9789.

9. Impulse response
Use `outputs/irf_npa_repo.png`; peak absolute response = 0.0555 after 4 quarters.

10. FEVD
Use `outputs/fevd_npa.png`; explain the medium-run variance shares for NPA across the three retained variables.

11. Answer to the question
Present the result bluntly: no meaningful Granger-causal evidence in either direction in this specification, and the repo-rate proxy is a major limitation.

12. Limitations and next steps
Interpolation, proxy rate series, and the dropped credit control; suggest robustness checks with a true RBI repo-rate dataset and a better-covered credit series.
Portmanteau test flags residual whiteness issue - standard caveat for interpolated short panels. A robustness check with true quarterly RBI repo and credit data would resolve this.