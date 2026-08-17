[README.md](https://github.com/user-attachments/files/31138151/README.md)
# Activity 1.4 – A database on individual ownership

## Household product ownership, use, and sharing potential across six European cities

This folder contains the data, analytical code, methodological documentation, and reproducibility materials supporting **Activity 1.4 – A database on individual ownership** of the Digital Kiosks project.

The accompanying study aims to better understand the ownership, use, and sharing potential of household products. Household survey data from six participating European cities were analysed to examine product ownership and underutilisation, differences between demographic groups, awareness and use of circular economy initiatives, willingness to borrow products, and motivations for and barriers to using sharing stations.

The participating cities are **Antwerpen, Bergen, Gothenburg, Hamburg, Saint Quentin, and Sint Niklaas**.

---

## Repository structure

The materials for Activity 1.4 are organised as follows:

```text
activity-1.4-individual-ownership/
│
├── README.md
├── requirements.txt
│
├── data/
│   └── analysis_ready/
│
├── scripts/
│   ├── report_analysis.py
│   └── harmonisation/
│
├── documentation/
│   ├── codebook.xlsx
│   ├── methodology_and_processing.md
│   ├── report_output_manifest.md
│   ├── report_to_code_verification.md
│   └── analysis_code_audit.md
│
└── outputs/
    ├── tables/
    └── figures/
```

---

## Data

The `data/analysis_ready/` folder contains the reduced analysis-ready datasets used for the final reporting analysis, where these data can be made publicly available.

The analysis covers six city datasets:

- Antwerpen
- Bergen
- Gothenburg
- Hamburg
- Saint Quentin
- Sint Niklaas

The analysis-ready datasets contain the variables required to reproduce the analyses presented in the report. They are derived from harmonised versions of the original city survey datasets.

The original survey exports and full harmonised datasets are not required to reproduce the final reporting analysis and are therefore not included in the public reporting package.

A description of the variables included in the analysis-ready datasets is provided in the [codebook](documentation/codebook.xlsx).

---

## Analytical workflow

The analytical workflow consists of two main stages: **data harmonisation** and **reporting analysis**.

### 1. Data harmonisation

The original city surveys differed in structure, variable names, response categories, and, in some cases, the household products included in the questionnaire.

City-specific harmonisation scripts were therefore used to map the original survey data to a common analytical structure.

These scripts are provided in:

`scripts/harmonisation/`

The harmonisation scripts document the transformation from the original city-specific survey variables to the variables used in the cross-city analysis.

### 2. Reporting analysis

The final analyses used in the Activity 1.4 report are reproduced by:

`scripts/report_analysis.py`

This is a cleaned reporting script containing the analytical procedures required to reproduce the core quantitative results presented in the report.

Exploratory analyses, intermediate development code, and outputs that were not used in the final report are intentionally excluded from this script.

The reporting analysis includes:

- household product ownership;
- underutilisation of privately owned products;
- comparison of ownership and underutilisation across cities;
- city-level estimates of underutilised products;
- the sharing-potential indicator;
- demographic associations with ownership and underutilisation;
- awareness and use of circular economy initiatives;
- use of sharing stations;
- motivations for borrowing from sharing stations; and
- barriers to borrowing from sharing stations.

Further details on the analytical decisions are provided in [Methodology and processing](documentation/methodology_and_processing.md).

---

## Reproducing the analysis

The main reporting analysis can be reproduced directly from the analysis-ready datasets.

### 1. Create a Python environment

A separate virtual environment is recommended.

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install the required Python packages

From the Activity 1.4 directory, run:

```bash
pip install -r requirements.txt
```

### 3. Run the reporting analysis

Run:

```bash
python scripts/report_analysis.py
```

The script reads the analysis-ready city datasets and generates the analytical tables and figures used for reporting.

Generated outputs are written to:

```text
outputs/
├── tables/
└── figures/
```

The relationship between the generated outputs and the corresponding tables and figures in the report is documented in the [Report output manifest](documentation/report_output_manifest.md).

---

## Documentation

Supporting methodological and reproducibility documentation is provided in the `documentation/` folder.

### Codebook

[`documentation/codebook.xlsx`](documentation/codebook.xlsx)

Provides the variable definitions and coding used in the analysis-ready datasets.

### Methodology and processing

[`documentation/methodology_and_processing.md`](documentation/methodology_and_processing.md)

Documents the principal methodological decisions, operational definitions, assumptions, data-processing procedures, and analytical choices used in the study.

### Report output manifest

[`documentation/report_output_manifest.md`](documentation/report_output_manifest.md)

Links the tables and figures presented in the report to the corresponding outputs generated by the reporting script.

### Report-to-code verification

[`documentation/report_to_code_verification.md`](documentation/report_to_code_verification.md)

Documents the verification of the cleaned analytical pipeline against the quantitative results used in the report.

### Analysis code audit

[`documentation/analysis_code_audit.md`](documentation/analysis_code_audit.md)

Documents the scope of the cleaned reporting script and identifies analyses and development outputs that were intentionally excluded because they were not used in the final report.

---

## Key methodological considerations

Several methodological choices are important when interpreting the results.

### Underutilisation

Underutilisation was assessed at the respondent-item level.

An owned item was classified as underutilised when the respondent reported using it **never** or **less than once per month**.

This threshold is an operational definition developed for this study and should not be interpreted as a universally established definition of household product underutilisation.

### Differences in products between cities

Not all household products were included in every city survey.

Cross-city averages therefore only include cities in which the corresponding product was surveyed. A product that was not included in a particular city questionnaire is treated as unavailable for that comparison rather than as having zero ownership or use.

### City-level estimates

City-level estimates extrapolate observed survey ownership and underutilisation patterns to the number of households in each participating city.

These estimates are intended to illustrate the potential scale of product underutilisation at city level. They should be interpreted as indicative estimates rather than precise population counts, as they depend on the assumption that the survey sample reasonably approximates ownership and use patterns in the wider city population.

### Sharing-potential indicator

The sharing-potential indicator combines ownership, underutilisation and stated willingness to borrow. It is intended as a comparative prioritisation measure and should not be interpreted as a validated prediction of actual demand or sharing-station performance.

The indicator is intended as a comparative prioritisation measure and should not be interpreted as a validated prediction of actual demand for or performance of a sharing station.

### Borrowing willingness

Reported willingness to borrow represents stated intention rather than observed future borrowing behaviour.

Actual use of a sharing station may also depend on factors such as accessibility, distance, opening hours, product availability, trust, convenience, and borrowing procedures.

### Motivations and barriers

Respondents could select multiple motivations for or barriers to using sharing stations.

Percentages therefore represent the proportion of respondents within the relevant user or non-user group selecting each reason and do not sum to 100%.

Pooled percentages describe the complete respondent sample and are therefore respondent-weighted. City-specific percentages should be used when comparing participating cities.

---

## Demographic analysis

Associations between demographic characteristics and product ownership and underutilisation were analysed using pooled respondent-item models.

Generalised Estimating Equations (GEE) were used to account for repeated product observations belonging to the same respondent.

The models examine associations with:

- income;
- age;
- gender; and
- education.

For the demographic analysis, the harmonised five-category income variable was grouped into three categories:

- below median;
- around median; and
- above median.

The statistical results should be interpreted as associations and not as evidence of causal relationships.

Further model specifications are documented in [Methodology and processing](documentation/methodology_and_processing.md).

---

## Reproducibility and verification

The cleaned reporting pipeline was rerun from the six analysis-ready city datasets and compared with the quantitative results used in the final report.

The verification included checks of, among others:

- total respondent numbers;
- respondent-item observations used in the statistical models;
- ownership and underutilisation results;
- adjusted demographic estimates;
- GEE model results;
- initiative-awareness and use results;
- sharing-station user and non-user counts; and
- pooled motivations and barriers.

The verification process is documented in:

**[Report-to-code verification](documentation/report_to_code_verification.md)**

The relationship between report elements and generated analytical outputs is documented separately in:

**[Report output manifest](documentation/report_output_manifest.md)**

Together, the analysis-ready data, reporting script, methodological documentation, output manifest, and verification materials provide a transparent link between the underlying analytical workflow and the results presented in the report.

---

## Outputs

The `outputs/` directory contains tables and figures generated by the cleaned reporting analysis.

### Tables

`outputs/tables/`

Contains processed tables supporting the quantitative results presented in the report.

### Figures

`outputs/figures/`

Contains figures generated from the analysis-ready datasets and used in the report.

These outputs are included to facilitate verification of the analysis and comparison with the published report.

---

## Data protection and availability

The analysis-ready datasets are reduced versions of the harmonised survey datasets and contain only variables required for the reported analyses.

The original survey exports and full harmonised datasets contain additional information that is not required for reproduction of the report and are therefore not intended for public distribution through this repository.

---

## Software requirements

The analysis was conducted in Python.

Required Python packages and versions are specified in:

[`requirements.txt`](requirements.txt)

Installing these dependencies before running `scripts/report_analysis.py` is recommended to support reproducibility of the analytical environment.

---

## Report

These materials support the Digital Kiosks Activity 1.4 report:

**Understanding household product ownership, use, and opportunities to support neighbourhood sharing stations**

*A study conducted in six European cities*

A permanent link to the final report can be added here once available.

---

## Citation

When referring to these materials, please identify them as supporting research materials for:

**Digital Kiosks – Activity 1.4: A database on individual ownership**

If the repository is archived through a research repository such as Zenodo, the corresponding DOI and recommended citation can be added here.

---

## Contact

For questions regarding the research, analytical methods, or supporting materials, please refer to the contact information provided in the accompanying Digital Kiosks report.
