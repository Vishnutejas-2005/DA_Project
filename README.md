# Project: RBI Rate Policy vs Bank Stress

This repo contains a full end-to-end analysis based on the provided data files and the project explainer.

## Quick start
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python analysis.py
```

## Outputs
Generated files are written to `outputs/`:
- `cleaned_quarterly.csv`
- `cleaned_quarterly_differenced.csv`
- `timeline.png`
- `irf_npa_repo.png`
- `fevd_npa.png`
- `adf_results.csv`
- `granger_results.csv`
- `var_lag_order.csv`
- `var_diagnostics.csv`

## Report and slides
- `report.md` contains the written analysis summary.
- `slides.md` contains a 10–12 slide outline referencing the generated plots.

## Notes
- Annual World Bank data is interpolated to quarterly frequency.
- Repo rate is proxied using the real interest rate series provided in the data folder.
# DA_Project
