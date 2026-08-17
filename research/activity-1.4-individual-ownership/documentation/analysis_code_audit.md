# Analysis-code audit

## Retained in the clean reporting script

The final `report_analysis.py` retains the analyses that are directly used in the report:

1. Item ownership rates.
2. Underutilisation rates among owners.
3. City-level estimates of owned and underutilised products.
4. Indicative storage-volume and replacement-value estimates.
5. Borrowing willingness, product suitability and the sharing potential index.
6. Cross-city ownership, underutilisation and sharing-potential figures.
7. Pooled respondent-item GEE models for ownership and underutilisation.
8. Adjusted predicted probabilities by income with robust 95% confidence intervals.
9. Circular-economy initiative awareness/use funnel.
10. Sharing-station motivations and barriers.
11. Master city-item table used as the numerical backbone of the report and appendices.

## Excluded from the clean reporting script

The development analysis script contained useful exploratory or dashboard components that are not required to reproduce the final report. These have intentionally not been carried into `report_analysis.py`:

- Streamlit dashboard code and dashboard-only helpers.
- Portfolio/bubble scatterplots.
- Borrowing decomposition by owners versus non-owners.
- Conditional initiative-use heatmaps, e.g. P(Use B | Use A).
- Counts/profiles of the number of initiatives used per respondent.
- Coded open-text exploratory tables not reported in the final report.
- Expected-effects analyses not included in Activity 1.4 reporting.
- Duplicate/alternative plotting functions created during development.
- Development-only debug output and intermediate exports.

The original full analysis script should be retained in the internal project archive or version-control history, but the concise reporting script should be the primary analytical script distributed with the final report.
