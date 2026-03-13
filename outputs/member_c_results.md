# Member C Deliverable

## Results
- Repo rate -> NPA Granger test: F = 0.0033, p = 0.9541.
- NPA -> repo rate Granger test: F = 1.1758, p = 0.2793.
- IRF peak absolute NPA response occurs after 8 quarters with magnitude -0.0170.
- IRF chart saved to `outputs/irf_npa_repo.png`.
- FEVD chart saved to `outputs/fevd_npa.png`.

## FEVD at 8 Quarters
- npa_ratio: 0.926
- repo_rate: 0.020
- gdp_growth: 0.009
- credit_growth: 0.046

## Conclusion Paragraph
In this specification, the data do not provide statistically significant Granger-causal evidence in either direction between the repo-rate proxy and the NPA ratio at the 5% level. The impulse response is modest and the FEVD shows that medium-run NPA forecast variance is dominated by the NPA series' own shocks, with only a small share coming from the repo-rate proxy. Given the annual-to-quarterly interpolation and the use of a real-interest-rate proxy instead of the literal RBI repo series, the correct presentation is cautious: we find weak directional evidence rather than a strong policy-causality claim.