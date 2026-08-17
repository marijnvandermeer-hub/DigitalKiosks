# Report-to-code verification

**Result: 43 checks passed; 5 report corrections identified.**

The cleaned pipeline was rerun from the six analysis-ready datasets and compared with the final report and available historical analysis outputs.

## Conclusion

The cleaned reproducibility package reproduces the core quantitative analyses used in the report. The issues below are inconsistencies in the report document itself and should be corrected before the official upload.

## Corrections required in the report

- **Overall column (Table 6)**: The report table currently contains an unweighted mean across cities, while its caption and narrative describe pooled percentages. Replace the Overall column with table_reasons_borrowing.csv and label it 'Overall (%)'.
- **Overall column (Table 7)**: The report table currently contains an unweighted mean across cities, while the narrative uses pooled percentages. Replace the Overall column with table_reasons_not_borrowing.csv and label it 'Overall (%)'.
- **Income terminology (Methodology)**: The report mixes 'average gross household income' with 'median'. The harmonised data, GEE categories and survey appendix use median-based wording. Make this consistent before publication.
- **Information-sheet appendix reference (Results 3.1.3)**: Change the text reference from Appendix E to Appendix F.
- **Initiative-adoption appendix reference (Results 3.2)**: Change Appendix H to Appendix G; Appendix H is sharing-station use.

## Verification table

| Section | Report element | Status | Note |
|---|---|---|---|
| Sample | Total respondents | PASS | Matches the report sample size. |
| GEE | Ownership respondent-item observations | PASS | Matches the final pooled ownership model. |
| GEE | Underutilisation owner-item observations | PASS | Matches the final pooled underutilisation model. |
| Table 3 | Vacuum cleaner: ownership | PASS | Matches report. |
| Table 3 | Vacuum cleaner: underutilisation | PASS | Matches report. |
| Table 3 | Hand sander: ownership | PASS | Matches report. |
| Table 3 | Hand sander: underutilisation | PASS | Matches report. |
| Table 3 | Pressure washer: ownership | PASS | Matches report. |
| Table 3 | Pressure washer: underutilisation | PASS | Matches report. |
| Table 3 | Table tennis paddles: ownership | PASS | Matches report. |
| Table 3 | Table tennis paddles: underutilisation | PASS | Matches report. |
| Table 3 | Drill: ownership | PASS | Matches report. |
| Table 3 | Drill: underutilisation | PASS | Matches report. |
| Figure 6 | Below median | PASS | Adjusted ownership probability reproduced. |
| Figure 6 | Around median | PASS | Adjusted ownership probability reproduced. |
| Figure 6 | Above median | PASS | Adjusted ownership probability reproduced. |
| Figure 7 | Below median | PASS | Adjusted underutilisation probability reproduced. |
| Figure 7 | Around median | PASS | Adjusted underutilisation probability reproduced. |
| Figure 7 | Above median | PASS | Adjusted underutilisation probability reproduced. |
| Table 4 | Ownership: Income Below median | PASS | Matches report. |
| Table 4 | Ownership: Income Around median | PASS | Matches report. |
| Table 4 | Ownership: Age 36–45 | PASS | Matches report. |
| Table 4 | Ownership: Age 46–55 | PASS | Matches report. |
| Table 4 | Ownership: Age 56–65 | PASS | Matches report. |
| Table 4 | Underutilisation: Gender Woman | PASS | Matches report. |
| Table 5 | Second-hand shops: use range | PASS | Matches report after rounding. |
| Table 5 | Sharing initiatives: use range | PASS | Matches report after rounding. |
| Table 5 | Renting initiatives: use range | PASS | Matches report after rounding. |
| Results 3.3 | Sharing-station users / non-users | PASS | Matches report. |
| Results 3.3 narrative | To reduce consumption and or support the environment | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To save money | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To have more goods available | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To play sports or relax | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To learn new things | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To support local cooperation and community building | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To create opportunities for myself | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | To meet people | PASS | Pooled user percentage reproduced. |
| Results 3.3 narrative | Lack of sharing stations | PASS | Pooled non-user percentage reproduced. |
| Results 3.3 narrative | Lack of information on offered products | PASS | Pooled non-user percentage reproduced. |
| Results 3.3 narrative | Lack of information on how sharing stations work | PASS | Pooled non-user percentage reproduced. |
| Results 3.3 narrative | I am used to owning goods | PASS | Pooled non-user percentage reproduced. |
| Results 3.3 narrative | I use my items so often that i rather own them | PASS | Pooled non-user percentage reproduced. |
| Item/city estimates | Historical item-ranking exports | PASS | Ownership, underutilisation, city estimates and borrowing willingness matched historical outputs. |
| Table 6 | Overall column | REPORT FIX NEEDED | The report table currently contains an unweighted mean across cities, while its caption and narrative describe pooled percentages. Replace the Overall column with table_reasons_borrowing.csv and label it 'Overall (%)'. |
| Table 7 | Overall column | REPORT FIX NEEDED | The report table currently contains an unweighted mean across cities, while the narrative uses pooled percentages. Replace the Overall column with table_reasons_not_borrowing.csv and label it 'Overall (%)'. |
| Methodology | Income terminology | REPORT FIX NEEDED | The report mixes 'average gross household income' with 'median'. The harmonised data, GEE categories and survey appendix use median-based wording. Make this consistent before publication. |
| Results 3.1.3 | Information-sheet appendix reference | REPORT FIX NEEDED | Change the text reference from Appendix E to Appendix F. |
| Results 3.2 | Initiative-adoption appendix reference | REPORT FIX NEEDED | Change Appendix H to Appendix G; Appendix H is sharing-station use. |