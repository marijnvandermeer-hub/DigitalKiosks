# Methodology and processing notes

## Analytical dataset
Six city-specific survey datasets were harmonised into a common analytical structure. Harmonised variables use common names for demographics, household-item ownership, use frequency, borrowing willingness, circular-economy initiative awareness/use, and sharing-station motivations/barriers.

## Item-level analysis
Ownership is the proportion of respondents who reported owning each item. Underutilisation is assessed among owners and is defined as use frequency of `never` or `less than once per month` (numeric frequency <= 2). This threshold is an operational definition developed for this study rather than a universally established literature threshold.

For Bergen, owned items with missing use-frequency information are classified as underutilised, following the predefined conservative rule documented in the report. In other cities, missing owner use-frequency is excluded from the underutilisation denominator.

## City-level estimates
Sample rates are multiplied by the estimated number of households in each city. The extrapolation assumes approximately one item per household per product category and does not capture multiple ownership. Storage volume and replacement value use common item proxy values across cities and should be interpreted as indicative.

## Sharing potential
Product suitability is calculated from ownership × underutilisation. The rationale is that products that are widely owned but used infrequently appear to fulfil a recognised household need while only being required occasionally, making them relevant to consider for shared-access alternatives. Borrowing willingness is used as an indicator of stated demand. The sharing potential index is the geometric mean of suitability and borrowing willingness.

## Initiative adoption
For the awareness/use funnel, reported use implies awareness. This is necessary because respondents were able to select `use` without separately selecting `know`. Each respondent is therefore classified as: uses; knows but does not use; or does not know.

## Sharing-station motivations and barriers
Respondents could select multiple reasons. Percentages are calculated within the user or non-user group and therefore do not sum to 100%. Overall percentages are respondent-weighted across cities; city-specific percentages should be used for comparisons between cities.

## Demographic analysis
The pooled GEE analysis uses respondent-item observations and clusters repeated product observations within respondents. Ownership is modelled for all respondent-item observations; underutilisation is modelled among owned items. Models include income, age, gender and education, with city and product category included as controls. Income is collapsed from five harmonised categories into three groups for regression: below median, around median, and above median.

## Translation and harmonisation
Questionnaires were administered in local languages. City-specific harmonisation scripts preserve the mapping from local/raw variables into the common analytical schema. Saint-Quentin additionally used programmatic translation during preprocessing; this step should be retained in the archive if the full raw-to-analysis pipeline is published.
