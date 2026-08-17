import os
import re
import pandas as pd
import numpy as np

# =========================
# Config
# =========================
INPUT = "data/raw/survey_data/Antwerpen.csv"
OUTPUT = "data/processed/survey_data/harmonized/Antwerpen_survey_harmonized.csv"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

CITY_NAME = "Antwerpen"

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

YESNO_NL = {
    "ja": "yes",
    "nee": "no",
    "yes": "yes",
    "no": "no",
    "y": "yes",
    "n": "no",
}

def clean_text(x):
    if pd.isna(x):
        return ""
    t = str(x)
    t = t.replace("\ufeff", "").replace("Â", "").replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def get_series(df: pd.DataFrame, col: str) -> pd.Series:
    return df[col] if col in df.columns else pd.Series(pd.NA, index=df.index)

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
    if s == "zeg ik liever niet":
        return "Prefer not to say"
    if s == "":
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
    if s == "":
        return np.nan
    return "Other"


def harmonize_education(x):
    s = clean_text(x).lower()

    if "lager onderwijs" in s:
        return "Primary education"

    if "secundair onderwijs" in s or "beroepssecundair onderwijs" in s:
        return "Secondary / vocational education"

    if "graduaat" in s or "bachelor" in s or "master" in s:
        return "Higher education"

    if "doctoraat" in s or "phd" in s:
        return "Doctorate / PhD"

    if s == "":
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
    if s == "":
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
RAW_COLS["I am aware of climate change"] = get_series(df, "V1_1")
RAW_COLS["I am aware of overconsumption"] = get_series(df, "V1_2")

# Q2 initiatives (know/use)
RAW_COLS["Do you know initiatives second-hand shops"] = get_series(df, "V2_1_A1")
RAW_COLS["Do you use them in your daily lives second-hand shops"] = get_series(df, "V2_1_A2")
RAW_COLS["Do you know initiatives sharing initiatives"] = get_series(df, "V2_2_A1")
RAW_COLS["Do you use them in your daily lives sharing initiatives"] = get_series(df, "V2_2_A2")
RAW_COLS["Do you know initiatives renting initiatives"] = get_series(df, "V2_3_A1")
RAW_COLS["Do you use them in your daily lives renting initiatives"] = get_series(df, "V2_3_A2")
RAW_COLS["Do you know initiatives repair shops"] = get_series(df, "V2_4_A1")
RAW_COLS["Do you use them in your daily lives repair shops"] = get_series(df, "V2_4_A2")

# Q3 own (checkbox)
RAW_COLS["Do you own the following goods?"] = "Checkbox block (see Own_* columns)"
RAW_COLS["Own_Hoover"] = get_series(df, "V3_A1")
RAW_COLS["Own_Steam cleaner"] = get_series(df, "V3_A2")
RAW_COLS["Own_Pressure washer"] = get_series(df, "V3_A3")
RAW_COLS["Own_Carpet cleaner"] = get_series(df, "V3_A4")
RAW_COLS["Own_Drill"] = get_series(df, "V3_A5")
RAW_COLS["Own_Hand sander"] = get_series(df, "V3_A6")
RAW_COLS["Own_Fitness equipment"] = get_series(df, "V3_A7")
RAW_COLS["Own_Table tennis"] = get_series(df, "V3_A8")
RAW_COLS["Own_Football & basketball"] = get_series(df, "V3_A9")
RAW_COLS["Own_Volleyball set"] = get_series(df, "V3_A10")
RAW_COLS["Own_Sewing machine"] = get_series(df, "V3_A11")
RAW_COLS["Own_Foldable chairs & table"] = get_series(df, "V3_A12")
RAW_COLS["Own_Video projector"] = get_series(df, "V3_A13")
RAW_COLS["Own_Partytent"] = get_series(df, "V3_A14")

# Q4 frequency (single-choice table) keep as text in RAW
RAW_COLS["Hoover"] = get_series(df, "V4_1")
RAW_COLS["Steam cleaner"] = get_series(df, "V4_2")
RAW_COLS["Pressure washer"] = get_series(df, "V4_3")
RAW_COLS["Carpet cleaner"] = get_series(df, "V4_4")
RAW_COLS["Drill"] = get_series(df, "V4_5")
RAW_COLS["Hand sander"] = get_series(df, "V4_6")
RAW_COLS["Fitness equipment"] = get_series(df, "V4_7")
RAW_COLS["Table tennis"] = get_series(df, "V4_8")
RAW_COLS["Football & basketball"] = get_series(df, "V4_9")
RAW_COLS["Volleyball set"] = get_series(df, "V4_10")
RAW_COLS["Sewing machine"] = get_series(df, "V4_11")
RAW_COLS["Foldable chairs & table"] = get_series(df, "V4_12")
RAW_COLS["Video projector"] = get_series(df, "V4_13")
RAW_COLS["Partytent"] = get_series(df, "V4_14")

# Q5 borrow consider (checkbox)
RAW_COLS["Which would you consider borrowing"] = "Checkbox block (see Borrow_* columns)"
RAW_COLS["Borrow_Hoover"] = get_series(df, "V5_A1")
RAW_COLS["Borrow_Steam cleaner"] = get_series(df, "V5_A2")
RAW_COLS["Borrow_Pressure washer"] = get_series(df, "V5_A3")
RAW_COLS["Borrow_Carpet cleaner"] = get_series(df, "V5_A4")
RAW_COLS["Borrow_Drill"] = get_series(df, "V5_A5")
RAW_COLS["Borrow_Hand sander"] = get_series(df, "V5_A6")
RAW_COLS["Borrow_Fitness equipment"] = get_series(df, "V5_A7")
RAW_COLS["Borrow_Table tennis"] = get_series(df, "V5_A8")
RAW_COLS["Borrow_Football & basketball"] = get_series(df, "V5_A9")
RAW_COLS["Borrow_Volleyball set"] = get_series(df, "V5_A10")
RAW_COLS["Borrow_Sewing machine"] = get_series(df, "V5_A11")
RAW_COLS["Borrow_Foldable chairs & table"] = get_series(df, "V5_A12")
RAW_COLS["Borrow_Video projector"] = get_series(df, "V5_A13")
RAW_COLS["Borrow_Partytent"] = get_series(df, "V5_A14")

# Q6
RAW_COLS["Have you ever borrowed an item from a sharing station?"] = get_series(df, "V6")

# Q7 reasons yes
RAW_COLS["What is/are your main reason(s) to borrow an item from a sharing station?"] = "Multi-select (see reason columns)"
RAW_COLS["To save money"] = get_series(df, "V7_A1")
RAW_COLS["To have more goods available"] = get_series(df, "V7_A2")
RAW_COLS["To play sports or relax"] = get_series(df, "V7_A3")
RAW_COLS["To learn new things"] = get_series(df, "V7_A4")
RAW_COLS["To create opportunities for myself"] = get_series(df, "V7_A5")
RAW_COLS["To meet people"] = get_series(df, "V7_A6")
RAW_COLS["To support local cooperation and community building"] = get_series(df, "V7_A7")
RAW_COLS["To support equal access to goods for everyone"] = get_series(df, "V7_A8")
RAW_COLS["To reduce consumption and/or support the environment"] = get_series(df, "V7_A9")
RAW_COLS["Other_REASONS_BORROW"] = get_series(df, "OPEN7_10")

# Q8 reasons no
RAW_COLS["What is/are your main reason(s) to not borrow an item from a sharing station?"] = "Multi-select (see NOT reason columns)"
RAW_COLS["Lack of sharing stations"] = get_series(df, "V8_A1")
RAW_COLS["Lack of information on how sharing stations work"] = get_series(df, "V8_A2")
RAW_COLS["Lack of information on offered products"] = get_series(df, "V8_A3")
RAW_COLS["Lack of product availability"] = get_series(df, "V8_A4")
RAW_COLS["Lack of quality and maintenance"] = get_series(df, "V8_A5")
RAW_COLS["Lack of hygiene"] = get_series(df, "V8_A6")
RAW_COLS["Time-consuming"] = get_series(df, "V8_A7")
RAW_COLS["It is too complicated"] = get_series(df, "V8_A8")
RAW_COLS["It is too expensive"] = get_series(df, "V8_A9")
RAW_COLS["I am used to owning goods"] = get_series(df, "V8_A10")
RAW_COLS["I use my items so often that I rather own them"] = get_series(df, "V8_A11")
RAW_COLS["I dont trust sharing station providers"] = get_series(df, "V8_A12")
RAW_COLS["I dont think it makes a difference for the environment"] = get_series(df, "V8_A13")
RAW_COLS["Other_NOT"] = get_series(df, "OPEN8_14")

# Q9
RAW_COLS["What item would you never share?"] = get_series(df, "V9")
RAW_COLS["NeverShare_Category"] = get_series(df, "V9").map(clean_text)


# demographics raw
RAW_COLS["postal code"] = get_series(df, "V11")
RAW_COLS["Gender"] = get_series(df, "V12")
RAW_COLS["Age"] = get_series(df, "V13")
RAW_COLS["Education"] = get_series(df, "V14")
RAW_COLS["Would you say your household income is"] = get_series(df, "V15")

# Create combined raw df
raw_df = pd.DataFrame({"Id": df[id_col]})
for k, v in RAW_COLS.items():
    raw_df[k] = v

# =========================
# 2) Harmonized block
# =========================
harm = pd.DataFrame(index=df.index)

harm["city"] = CITY_NAME
harm["postal_code"] = extract_postal(get_series(df, "V11"))
# Keep original demographic answers for QA
harm["gender_raw"] = get_series(df, "V12").map(clean_text)
harm["age_raw"] = get_series(df, "V13").map(clean_text)
harm["education_raw"] = get_series(df, "V14").map(clean_text)
harm["income_raw"] = get_series(df, "V15").map(clean_text)

# Harmonized demographic categories for cross-city analysis
harm["gender"] = harm["gender_raw"].map(harmonize_gender)
harm["age"] = harm["age_raw"].map(harmonize_age)
harm["education"] = harm["education_raw"].map(harmonize_education)
harm["income"] = harm["income_raw"].map(harmonize_income)

# borrowed
harm["borrowed_sharing_station"] = normalize_yesno(df["V6"]) if "V6" in df.columns else pd.NA

# initiatives
INIT_MAP = {
    "secondhand": ("V2_1_A1", "V2_1_A2"),
    "sharing": ("V2_2_A1", "V2_2_A2"),
    "renting": ("V2_3_A1", "V2_3_A2"),
    "repair": ("V2_4_A1", "V2_4_A2"),
}
for key, (kcol, ucol) in INIT_MAP.items():
    harm[f"know__{key}"] = checkbox_to_01(df[kcol]) if kcol in df.columns else 0
    harm[f"use__{key}"] = checkbox_to_01(df[ucol]) if ucol in df.columns else 0

# items
ITEMS = [
    ("vacuum_cleaner", "V3_A1", "V4_1", "V5_A1"),
    ("steam_cleaner", "V3_A2", "V4_2", "V5_A2"),
    ("pressure_washer", "V3_A3", "V4_3", "V5_A3"),
    ("carpet_cleaner", "V3_A4", "V4_4", "V5_A4"),
    ("drill", "V3_A5", "V4_5", "V5_A5"),
    ("hand_sander", "V3_A6", "V4_6", "V5_A6"),
    ("fitness_equipment", "V3_A7", "V4_7", "V5_A7"),
    ("table_tennis", "V3_A8", "V4_8", "V5_A8"),
    ("football_basketball", "V3_A9", "V4_9", "V5_A9"),
    ("volleyball_set", "V3_A10", "V4_10", "V5_A10"),
    ("sewing_machine", "V3_A11", "V4_11", "V5_A11"),
    ("foldable_chairs_table", "V3_A12", "V4_12", "V5_A12"),
    ("video_projector", "V3_A13", "V4_13", "V5_A13"),
    ("party_tent", "V3_A14", "V4_14", "V5_A14"),
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
    "reason_yes__to_save_money": "V7_A1",
    "reason_yes__to_have_more_goods_available": "V7_A2",
    "reason_yes__to_play_sports_or_relax": "V7_A3",
    "reason_yes__to_learn_new_things": "V7_A4",
    "reason_yes__to_create_opportunities_for_myself": "V7_A5",
    "reason_yes__to_meet_people": "V7_A6",
    "reason_yes__to_support_local_cooperation_and_community_building": "V7_A7",
    "reason_yes__to_support_equal_access_to_goods_for_everyone": "V7_A8",
    "reason_yes__to_reduce_consumption_and_or_support_the_environment": "V7_A9",
}
for out_col, src in YES_REASONS_MAP.items():
    harm[out_col] = checkbox_to_01(df[src]) if src in df.columns else 0

# reasons no
NO_REASONS_MAP = {
    "reason_no__lack_of_sharing_stations": "V8_A1",
    "reason_no__lack_of_information_on_how_sharing_stations_work": "V8_A2",
    "reason_no__lack_of_information_on_offered_products": "V8_A3",
    "reason_no__lack_of_product_availability": "V8_A4",
    "reason_no__lack_of_quality_and_maintenance": "V8_A5",
    "reason_no__lack_of_hygiene": "V8_A6",
    "reason_no__time_consuming": "V8_A7",
    "reason_no__it_is_too_complicated": "V8_A8",
    "reason_no__it_is_too_expensive": "V8_A9",
    "reason_no__i_am_used_to_owning_goods": "V8_A10",
    "reason_no__i_use_my_items_so_often_that_i_rather_own_them": "V8_A11",
    "reason_no__i_dont_trust_sharing_station_providers": "V8_A12",
    "reason_no__i_dont_think_it_makes_a_difference_for_the_environment": "V8_A13",
}
for out_col, src in NO_REASONS_MAP.items():
    harm[out_col] = checkbox_to_01(df[src]) if src in df.columns else 0

harm["other_reason_borrow_category"] = get_series(df, "OPEN7_10").map(clean_text)
harm["other_not_category"] = get_series(df, "OPEN8_14").map(clean_text)
harm["nevershare_category"] = get_series(df, "V9").map(clean_text)

# =========================
# 3) Combine (RAW first, then harmonized)
# =========================
combined = pd.concat([raw_df, harm], axis=1)

combined.to_csv(OUTPUT, index=False)
print(f"Saved combined raw+harmonized {CITY_NAME} dataset to: {OUTPUT}")

# Quick QA checks
print("\nQA: initiative columns unique values (know__secondhand):")
print(combined["know__secondhand"].value_counts(dropna=False).head())

print("\nQA: checkbox raw (Own_Hoover) unique values:")
print(combined["Own_Hoover"].value_counts(dropna=False).head())

print("\nQA: harmonized own__vacuum_cleaner unique values:")
print(combined["own__vacuum_cleaner"].value_counts(dropna=False).head())

print("\nQA: borrowed_sharing_station unique values:")
print(combined["borrowed_sharing_station"].value_counts(dropna=False).head())

print("\nQA: postal_code sample:")
print(combined["postal_code"].head())
