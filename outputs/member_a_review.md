# Member A Review

Original repository check:
- Not fully complete as submitted: the repo already had the core data-engineering artifacts, but it did not explicitly close Member A's deliverables from the explainer: there was no checklist-style completion review and no short written timeline interpretation for handoff into the report/slides.

Current completion status after fixes:
- Week 1 complete: the three source files used in the final model are present in `data/`; the old credit file is still present but intentionally unused.
- Week 2 complete: merged quarterly dataset saved to `outputs/cleaned_quarterly.csv` with 72 rows and 3 columns.
- Week 3 complete: `outputs/timeline.png` marks the 2015-16 rate-hike window and the timeline paragraph is written below.
- Week 4 complete: differenced dataset saved to `outputs/cleaned_quarterly_differenced.csv`.
- Week 5 support complete: Data section is written into `report.md`.
- Week 6 support complete: slides 1-3 content is present in `slides.md`.

Timeline paragraph:
The timeline shows a pronounced banking-stress cycle: the interpolated Gross NPA ratio rises from 3.23% in 2013Q1 to a local peak of 11.18% in 2018Q1. The repo-rate proxy is highest in 2015Q4 and remains elevated through the 2015-16 policy-tightening window (about 6.91% in 2015Q1 and 6.23% in 2016Q4). GDP growth also softens around the same period, so the visual story is consistent with a broad macro-financial stress episode rather than a clean one-variable shock.