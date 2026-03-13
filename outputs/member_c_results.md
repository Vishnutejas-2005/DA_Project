# Member C Deliverable

## Results
- Repo rate -> NPA Granger test: F = 1.8711, p = 0.1729.
- NPA -> repo rate Granger test: F = 0.0570, p = 0.8115.
- IRF peak absolute NPA response occurs after 4 quarters with magnitude 0.0797.
- IRF chart saved to `outputs/irf_npa_repo.png`.
- FEVD chart saved to `outputs/fevd_npa.png`.

## FEVD at 8 Quarters
- npa_ratio: 0.897
- repo_rate: 0.094
- gdp_growth: 0.009

## Conclusion Paragraph
In this specification, the data do not provide statistically significant Granger-causal evidence in either direction between the repo-rate proxy and the NPA ratio at the 5% level. The repo-to-NPA result in particular shows essentially no predictive power in this setup, with p = 0.1729. The impulse response is modest and the FEVD shows that medium-run NPA forecast variance is dominated by the NPA series' own shocks, with only a small share coming from the repo-rate proxy or GDP control. Given the annual-to-quarterly interpolation and the use of a real-interest-rate proxy instead of the literal RBI repo series, the correct presentation is cautious: we find no meaningful directional evidence here, and the proxy choice is a major limitation.