import os
import re
import pandas as pd
import numpy as np

# =========================
# Config
# =========================
INPUT = "data/raw/survey_data/SintNiklaas.csv"
OUTPUT = "data/processed/survey_data/harmonized/SintNiklaas_survey_harmonized.csv"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

CITY_NAME = "SintNiklaas"

# =========================
# Helpers
# =========================
FREQ_MAP_NL = {
    "dagelijks": 5,
    "wekelijks": 4,
    "maandelijks": 3,
    "minder dan maandelijks": 2,
    "nooit": 1,
}

YESNO_NL = {"ja": "yes", "nee": "no", "yes": "yes", "no": "no", "y": "yes", "n": "no"}

def clean_text(x):
    if pd.isna(x):
        return ""
    t = str(x)
    t = t.replace("\ufeff", "").replace("Â", "").replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def checkbox_to_01(series: pd.Series) -> pd.Series:
    """
    For checkbox/multi-response fields where:
    - 1 means checked
    - -99 means not checked
    - blanks/NaN treated as 0
    """
    s = pd.to_numeric(series, errors="coerce")
    s = s.replace(-99, 0).fillna(0)
    return s.where(s.isin([0, 1]), 0)

def map_freq(series: pd.Series) -> pd.Series:
    """
    Map Dutch frequency labels to numeric:
    5 daily, 4 weekly, 3 monthly, 2 less than monthly, 1 never
    """
    t = series.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    out = t.map(FREQ_MAP_NL)
    out2 = pd.to_numeric(t, errors="coerce")
    return out.fillna(out2)

def normalize_yesno(series: pd.Series) -> pd.Series:
    t = series.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    return t.map(YESNO_NL)

def extract_postal(series: pd.Series) -> pd.Series:
    return series.astype(str).str.extract(r"(\d{4,5})", expand=False)

def harmonize_gender(x):
    s = clean_text(x).lower()
    if s == "vrouw":
        return "Woman"
    if s == "man":
        return "Man"
    if s == "ander":
        return "Other"
    if "zeg ik liever niet" in s:
        return "Prefer not to say"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_age(x):
    s = clean_text(x).lower()
    s = s.replace("â€“", "-").replace("–", "-").replace("jaar", "").strip()
    s = re.sub(r"\s+", " ", s)

    if "18" in s and "25" in s:
        return "18–25"
    if "26" in s and "35" in s:
        return "26–35"
    if "36" in s and "45" in s:
        return "36–45"
    if "46" in s and "55" in s:
        return "46–55"
    if "56" in s and "65" in s:
        return "56–65"
    if "65+" in s:
        return "65+"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_education(x):
    s = clean_text(x).lower()

    if "lager" in s:
        return "Primary education"
    if "secundair" in s or "beroepssecundair" in s:
        return "Secondary / vocational education"
    if "graduaat" in s or "bachelor" in s or "master" in s:
        return "Higher education"
    if "doctoraat" in s or "phd" in s:
        return "Doctorate / PhD"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_income(x):
    s = clean_text(x).lower()

    if "ver onder" in s:
        return "Well below median"
    if "iets onder" in s:
        return "Slightly below median"
    if "ongeveer rond" in s:
        return "Around median"
    if "iets boven" in s:
        return "Slightly above median"
    if "ver boven" in s:
        return "Well above median"
    if s in {"", "nan"}:
        return np.nan
    return "Other"

# =========================
# Load
# =========================
df = pd.read_csv(INPUT)
df.columns = df.columns.str.strip()

# -------------------------
# Identify an ID column if present; else create one
# -------------------------
ID_CANDIDATES = ["Id", "ID", "ResponseId", "response_id", "RespondentID", "Respondent Id"]
id_col = next((c for c in ID_CANDIDATES if c in df.columns), None)
if id_col is None:
    df.insert(0, "Id", np.arange(1, len(df) + 1))
    id_col = "Id"

# =========================
# 1) Build RAW (human readable) columns for QA
# =========================
RAW_COLS = {}

# Q1 awareness
RAW_COLS["I am aware of climate change"] = df["V1_1"] if "V1_1" in df.columns else pd.NA
RAW_COLS["I am aware of overconsumption"] = df["V1_2"] if "V1_2" in df.columns else pd.NA

# Q2 initiatives (know/use)
RAW_COLS["Do you know initiatives second-hand shops"] = df["V2_1_A1"] if "V2_1_A1" in df.columns else pd.NA
RAW_COLS["Do you use them in your daily lives second-hand shops"] = df["V2_1_A2"] if "V2_1_A2" in df.columns else pd.NA
RAW_COLS["Do you know initiatives sharing initiatives"] = df["V2_2_A1"] if "V2_2_A1" in df.columns else pd.NA
RAW_COLS["Do you use them in your daily lives sharing initiatives"] = df["V2_2_A2"] if "V2_2_A2" in df.columns else pd.NA
RAW_COLS["Do you know initiatives renting initiatives"] = df["V2_3_A1"] if "V2_3_A1" in df.columns else pd.NA
RAW_COLS["Do you use them in your daily lives renting initiatives"] = df["V2_3_A2"] if "V2_3_A2" in df.columns else pd.NA
RAW_COLS["Do you know initiatives repair shops"] = df["V2_4_A1"] if "V2_4_A1" in df.columns else pd.NA
RAW_COLS["Do you use them in your daily lives repair shops"] = df["V2_4_A2"] if "V2_4_A2" in df.columns else pd.NA

# Q3
RAW_COLS["Do you think you own underutilized goods?"] = df["V3_1"] if "V3_1" in df.columns else pd.NA

# Q4 own (checkbox)
RAW_COLS["Do you own the following goods?"] = "Checkbox block (see Own_* columns)"
RAW_COLS["Own_Hoover"] = df["V4_A1"] if "V4_A1" in df.columns else pd.NA
RAW_COLS["Own_Steam cleaner"] = df["V4_A2"] if "V4_A2" in df.columns else pd.NA
RAW_COLS["Own_Pressure washer"] = df["V4_A3"] if "V4_A3" in df.columns else pd.NA
RAW_COLS["Own_Carpet cleaner"] = df["V4_A4"] if "V4_A4" in df.columns else pd.NA
RAW_COLS["Own_Drill"] = df["V4_A5"] if "V4_A5" in df.columns else pd.NA
RAW_COLS["Own_Hand sander"] = df["V4_A6"] if "V4_A6" in df.columns else pd.NA
RAW_COLS["Own_Fitness equipment"] = df["V4_A7"] if "V4_A7" in df.columns else pd.NA
RAW_COLS["Own_Table tennis"] = df["V4_A8"] if "V4_A8" in df.columns else pd.NA
RAW_COLS["Own_Football & basketball"] = df["V4_A9"] if "V4_A9" in df.columns else pd.NA
RAW_COLS["Own_Volleyball set"] = df["V4_A10"] if "V4_A10" in df.columns else pd.NA

# Q5 frequency (single-choice table) keep as text in RAW
RAW_COLS["Hoover"] = df["V5_1"] if "V5_1" in df.columns else pd.NA
RAW_COLS["Steam cleaner"] = df["V5_2"] if "V5_2" in df.columns else pd.NA
RAW_COLS["Pressure washer"] = df["V5_3"] if "V5_3" in df.columns else pd.NA
RAW_COLS["Carpet cleaner"] = df["V5_4"] if "V5_4" in df.columns else pd.NA
RAW_COLS["Drill"] = df["V5_5"] if "V5_5" in df.columns else pd.NA
RAW_COLS["Hand sander"] = df["V5_6"] if "V5_6" in df.columns else pd.NA
RAW_COLS["Fitness equipment"] = df["V5_7"] if "V5_7" in df.columns else pd.NA
RAW_COLS["Table tennis"] = df["V5_8"] if "V5_8" in df.columns else pd.NA
RAW_COLS["Football & basketball"] = df["V5_9"] if "V5_9" in df.columns else pd.NA
RAW_COLS["Volleyball set"] = df["V5_10"] if "V5_10" in df.columns else pd.NA

# Q6 borrow consider (checkbox)
RAW_COLS["Which would you consider borrowing"] = "Checkbox block (see Borrow_* columns)"
RAW_COLS["Borrow_Hoover"] = df["V6_A1"] if "V6_A1" in df.columns else pd.NA
RAW_COLS["Borrow_Steam cleaner"] = df["V6_A2"] if "V6_A2" in df.columns else pd.NA
RAW_COLS["Borrow_Pressure washer"] = df["V6_A3"] if "V6_A3" in df.columns else pd.NA
RAW_COLS["Borrow_Carpet cleaner"] = df["V6_A4"] if "V6_A4" in df.columns else pd.NA
RAW_COLS["Borrow_Drill"] = df["V6_A5"] if "V6_A5" in df.columns else pd.NA
RAW_COLS["Borrow_Hand sander"] = df["V6_A6"] if "V6_A6" in df.columns else pd.NA
RAW_COLS["Borrow_Fitness equipment"] = df["V6_A7"] if "V6_A7" in df.columns else pd.NA
RAW_COLS["Borrow_Table tennis"] = df["V6_A8"] if "V6_A8" in df.columns else pd.NA
RAW_COLS["Borrow_Football & basketball"] = df["V6_A9"] if "V6_A9" in df.columns else pd.NA
RAW_COLS["Borrow_Volleyball set"] = df["V6_A10"] if "V6_A10" in df.columns else pd.NA

# Q7
RAW_COLS["Have you ever borrowed an item from a sharing station?"] = df["V7"] if "V7" in df.columns else pd.NA

# Q8
RAW_COLS["What is/are your main reason(s) to borrow an item from a sharing station?"] = "Multi-select (see reason columns)"
RAW_COLS["To save money"] = df["V8_A1"] if "V8_A1" in df.columns else pd.NA
RAW_COLS["To have more goods available"] = df["V8_A2"] if "V8_A2" in df.columns else pd.NA
RAW_COLS["To play sports or relax"] = df["V8_A3"] if "V8_A3" in df.columns else pd.NA
RAW_COLS["To learn new things"] = df["V8_A4"] if "V8_A4" in df.columns else pd.NA
RAW_COLS["To create opportunities for myself"] = df["V8_A5"] if "V8_A5" in df.columns else pd.NA
RAW_COLS["To meet people"] = df["V8_A6"] if "V8_A6" in df.columns else pd.NA
RAW_COLS["To support local cooperation and community building"] = df["V8_A7"] if "V8_A7" in df.columns else pd.NA
RAW_COLS["To support equal access to goods for everyone"] = df["V8_A8"] if "V8_A8" in df.columns else pd.NA
RAW_COLS["To reduce consumption and/or support the environment"] = df["V8_A9"] if "V8_A9" in df.columns else pd.NA
RAW_COLS["Other_REASONS_BORROW"] = df["OPEN8_10"] if "OPEN8_10" in df.columns else pd.NA

# Q9
RAW_COLS["What is/are your main reason(s) to not borrow an item from a sharing station?"] = "Multi-select (see NOT reason columns)"
RAW_COLS["Lack of sharing stations"] = df["V9_A1"] if "V9_A1" in df.columns else pd.NA
RAW_COLS["Lack of information on how sharing stations work"] = df["V9_A2"] if "V9_A2" in df.columns else pd.NA
RAW_COLS["Lack of information on offered products"] = df["V9_A3"] if "V9_A3" in df.columns else pd.NA
RAW_COLS["Lack of product availability"] = df["V9_A4"] if "V9_A4" in df.columns else pd.NA
RAW_COLS["Lack of quality and maintenance"] = df["V9_A5"] if "V9_A5" in df.columns else pd.NA
RAW_COLS["Lack of hygiene"] = df["V9_A6"] if "V9_A6" in df.columns else pd.NA
RAW_COLS["Time-consuming"] = df["V9_A7"] if "V9_A7" in df.columns else pd.NA
RAW_COLS["It is too complicated"] = df["V9_A8"] if "V9_A8" in df.columns else pd.NA
RAW_COLS["It is too expensive"] = df["V9_A9"] if "V9_A9" in df.columns else pd.NA
RAW_COLS["I am used to owning goods"] = df["V9_A10"] if "V9_A10" in df.columns else pd.NA
RAW_COLS["I use my items so often that I rather own them"] = df["V9_A11"] if "V9_A11" in df.columns else pd.NA
RAW_COLS["I dont trust sharing station providers"] = df["V9_A12"] if "V9_A12" in df.columns else pd.NA
RAW_COLS["I dont think it makes a difference for the environment"] = df["V9_A13"] if "V9_A13" in df.columns else pd.NA
RAW_COLS["Other_NOT"] = df["OPEN9_14"] if "OPEN9_14" in df.columns else pd.NA

# Q10
RAW_COLS["What item would you never share?"] = df["V10"] if "V10" in df.columns else pd.NA
RAW_COLS["NeverShare_Category"] = df["V10"].map(clean_text) if "V10" in df.columns else pd.NA

# Q11 societal (12 items) -> keep as separate raw cols
Q11_LABELS = [
    "Peoples awareness of the impact of consumption is",
    "Equality in peoples access to goods is",
    "Peoples access to social activities is",
    "Peoples chances to meet people are",
    "The sense of community in my neigbourhood is",
    "Peoples ability to learn new skills is",
    "Free space in peoples homes is",
    "Peoples ability to maintain and clean their homes is",
    "The amount of recycling / reducing waste in my neigbourhood is",
    "The amount of waste people create is",
    "The needs of my community are valued",
    "My needs are valued",
]
for i, lab in enumerate(Q11_LABELS, start=1):
    RAW_COLS[lab] = df.get(f"V11_{i}", pd.NA)

# Q12 expected effects (5)
Q12_LABELS = [
    ("The amount of jobs will", "V12_1"),
    ("Household spending on goods will", "V12_2"),
    ("The amount of new businesses and profits will", "V12_3"),
    ("The amount of shaveing information through platforms / apps will", "V12_4"),
    ("The negative environmental impact will", "V12_5"),
]
for lab, src in Q12_LABELS:
    RAW_COLS[lab] = df.get(src, pd.NA)

# demographics raw
RAW_COLS["postal code"] = df.get("V13", pd.NA)
RAW_COLS["Gender"] = df.get("V14", pd.NA)
RAW_COLS["Age"] = df.get("V15", pd.NA)
RAW_COLS["Education"] = df.get("V16", pd.NA)
RAW_COLS["Would you say your household income is"] = df.get("V17", pd.NA)

# Create combined raw df
raw_df = pd.DataFrame({ "Id": df[id_col] })
for k, v in RAW_COLS.items():
    raw_df[k] = v

# =========================
# 2) Harmonized block (same as your other file)
# =========================
harm = pd.DataFrame(index=df.index)

harm["city"] = CITY_NAME
harm["gender_raw"] = df.get("V14", pd.Series([pd.NA] * len(df))).map(clean_text)
harm["age_raw"] = df.get("V15", pd.Series([pd.NA] * len(df))).map(clean_text)
harm["education_raw"] = df.get("V16", pd.Series([pd.NA] * len(df))).map(clean_text)
harm["income_raw"] = df.get("V17", pd.Series([pd.NA] * len(df))).map(clean_text)

harm["gender"] = harm["gender_raw"].map(harmonize_gender)
harm["age"] = harm["age_raw"].map(harmonize_age)
harm["education"] = harm["education_raw"].map(harmonize_education)
harm["income"] = harm["income_raw"].map(harmonize_income)
harm["postal_code"] = extract_postal(df.get("V13", pd.Series([pd.NA]*len(df))))

# borrowed (keep yes/no normalized)
harm["borrowed_sharing_station"] = normalize_yesno(df["V7"]) if "V7" in df.columns else pd.NA

# initiatives
INIT_MAP = {
    "secondhand": ("V2_1_A1", "V2_1_A2"),
    "sharing":    ("V2_2_A1", "V2_2_A2"),
    "renting":    ("V2_3_A1", "V2_3_A2"),
    "repair":     ("V2_4_A1", "V2_4_A2"),
}
for key, (kcol, ucol) in INIT_MAP.items():
    harm[f"know__{key}"] = checkbox_to_01(df[kcol]) if kcol in df.columns else 0
    harm[f"use__{key}"]  = checkbox_to_01(df[ucol]) if ucol in df.columns else 0

# items
ITEMS = [
    ("vacuum_cleaner",      "V4_A1",  "V5_1",  "V6_A1"),
    ("steam_cleaner",       "V4_A2",  "V5_2",  "V6_A2"),
    ("pressure_washer",     "V4_A3",  "V5_3",  "V6_A3"),
    ("carpet_cleaner",      "V4_A4",  "V5_4",  "V6_A4"),
    ("drill",               "V4_A5",  "V5_5",  "V6_A5"),
    ("hand_sander",         "V4_A6",  "V5_6",  "V6_A6"),
    ("fitness_equipment",   "V4_A7",  "V5_7",  "V6_A7"),
    ("table_tennis",        "V4_A8",  "V5_8",  "V6_A8"),
    ("football_basketball", "V4_A9",  "V5_9",  "V6_A9"),
    ("volleyball_set",      "V4_A10", "V5_10", "V6_A10"),
]

own_cols, under_cols = [], []
for slug, own_c, freq_c, rent_c in ITEMS:
    harm[f"own__{slug}"] = checkbox_to_01(df[own_c]) if own_c in df.columns else 0
    harm[f"rent__{slug}"] = checkbox_to_01(df[rent_c]) if rent_c in df.columns else 0
    harm[f"usefreq__{slug}"] = map_freq(df[freq_c]) if freq_c in df.columns else np.nan

    own = harm[f"own__{slug}"]
    freq = harm[f"usefreq__{slug}"]
    harm[f"underutilized__{slug}"] = np.where(
        own == 1,
        np.where(pd.isna(freq), 1, np.where(freq <= 2, 1, 0)),
        np.nan
    )

    own_cols.append(f"own__{slug}")
    under_cols.append(f"underutilized__{slug}")

harm["ownership_count"] = harm[own_cols].fillna(0).sum(axis=1)
harm["underutilization_count"] = harm[under_cols].sum(axis=1)
harm["underutilization_index"] = np.where(
    harm["ownership_count"] > 0,
    harm["underutilization_count"] / harm["ownership_count"],
    np.nan
)

# reasons yes
YES_REASONS_MAP = {
    "reason_yes__to_save_money":  "V8_A1",
    "reason_yes__to_have_more_goods_available": "V8_A2",
    "reason_yes__to_play_sports_or_relax": "V8_A3",
    "reason_yes__to_learn_new_things": "V8_A4",
    "reason_yes__to_create_opportunities_for_myself": "V8_A5",
    "reason_yes__to_meet_people": "V8_A6",
    "reason_yes__to_support_local_cooperation_and_community_building": "V8_A7",
    "reason_yes__to_support_equal_access_to_goods_for_everyone": "V8_A8",
    "reason_yes__to_reduce_consumption_and_or_support_the_environment": "V8_A9",
}
for out_col, src in YES_REASONS_MAP.items():
    harm[out_col] = checkbox_to_01(df[src]) if src in df.columns else 0

# reasons no
NO_REASONS_MAP = {
    "reason_no__lack_of_sharing_stations": "V9_A1",
    "reason_no__lack_of_information_on_how_sharing_stations_work": "V9_A2",
    "reason_no__lack_of_information_on_offered_products": "V9_A3",
    "reason_no__lack_of_product_availability": "V9_A4",
    "reason_no__lack_of_quality_and_maintenance": "V9_A5",
    "reason_no__lack_of_hygiene": "V9_A6",
    "reason_no__time_consuming": "V9_A7",
    "reason_no__it_is_too_complicated": "V9_A8",
    "reason_no__it_is_too_expensive": "V9_A9",
    "reason_no__i_am_used_to_owning_goods": "V9_A10",
    "reason_no__i_use_my_items_so_often_that_i_rather_own_them": "V9_A11",
    "reason_no__i_dont_trust_sharing_station_providers": "V9_A12",
    "reason_no__i_dont_think_it_makes_a_difference_for_the_environment": "V9_A13",
}
for out_col, src in NO_REASONS_MAP.items():
    harm[out_col] = checkbox_to_01(df[src]) if src in df.columns else 0

harm["other_not_category"] = df["OPEN9_14"].map(clean_text) if "OPEN9_14" in df.columns else ""
harm["nevershare_category"] = df["V10"].map(clean_text) if "V10" in df.columns else ""

# expected effects
EXPECT_MAP = {
    "expect__jobs": "V12_1",
    "expect__spending": "V12_2",
    "expect__business": "V12_3",
    "expect__platforms": "V12_4",
    "expect__neg_env_impact": "V12_5",
}
for out_col, src in EXPECT_MAP.items():
    harm[out_col] = pd.to_numeric(df[src], errors="coerce") if src in df.columns else np.nan

# =========================
# 3) Combine (RAW first, then harmonized)
# =========================
combined = pd.concat([raw_df, harm], axis=1)

combined.to_csv(OUTPUT, index=False)
print(f"Saved combined raw+harmonized Sint-Niklaas dataset to: {OUTPUT}")

# Quick QA checks
print("\nQA: initiative columns unique values (know__secondhand):", combined["know__secondhand"].value_counts(dropna=False).head())
print("QA: checkbox raw (Own_Hoover) unique values:", combined["Own_Hoover"].value_counts(dropna=False).head())
print("QA: harmonized own__vacuum_cleaner unique values:", combined["own__vacuum_cleaner"].value_counts(dropna=False).head())
