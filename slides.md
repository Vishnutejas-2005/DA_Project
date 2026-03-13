# Slide Outline (12 slides)

1. Title
Question: Does RBI rate policy cause bank stress, or does bank stress cause the RBI to act?

2. Why this matters
2013-2018 NPA spike, macro stress, and possible policy feedback.

3. Data
Four series, 2005Q1-2021Q4, RBI + World Bank, annual macro data interpolated to quarterly frequency.

4. Timeline plot
Use `outputs/timeline.png`; highlight the 2015-16 tightening window.

5. Stationarity results
Use `outputs/adf_results.csv`; explain which series were differenced.

6. VAR setup
Lag order = 1; explain why BIC/AIC was used and what a VAR does.

7. Diagnostics and stability
Use `outputs/var_stability.png` and the Durbin-Watson summary from `outputs/var_diagnostics.csv`.

8. Granger causality
Repo -> NPA p-value = 0.9541; NPA -> Repo p-value = 0.2793.

9. Impulse response
Use `outputs/irf_npa_repo.png`; peak absolute response = -0.0170 after 8 quarters.

10. FEVD
Use `outputs/fevd_npa.png`; explain the medium-run variance shares for NPA.

11. Answer to the question
Present the result cautiously: no strong Granger-causal evidence in either direction in this specification.

12. Limitations and next steps
Interpolation, proxy rate series, and possible robustness checks with a true RBI repo-rate dataset.