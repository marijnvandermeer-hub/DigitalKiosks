import os
import re
import pandas as pd
import numpy as np

INPUT = "data/processed/survey_data/City of Bergen - survey data_v_mvdm_processed.csv"
OUTPUT = "data/processed/survey_data/harmonized/Bergen_survey_harmonized.csv"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

FREQ_MAP = {
    "day": 5, "every day": 5, "everyday": 5,
    "week": 4, "every week": 4,
    "month": 3, "every month": 3,
    "less": 2, "less often": 2,
    "never": 1,
}

YESNO = {"yes": "yes", "y": "yes", "no": "no", "n": "no"}

def clean_text(x):
    if pd.isna(x):
        return ""
    t = str(x)
    t = t.replace("\ufeff", "").replace("Â", "").replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def normalize_yes_no_series(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    return t.map(YESNO)

def map_freq_series(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    return pd.to_numeric(t.replace(FREQ_MAP), errors="coerce")

def harmonize_gender(x):
    s = clean_text(x).lower()
    if s == "female":
        return "Woman"
    if s == "male":
        return "Man"
    if s == "other":
        return "Other"
    if s == "prefer not to share":
        return "Prefer not to say"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_age(x):
    s = clean_text(x).lower()
    s = s.replace("years", "").replace("year", "").strip()
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
    if "66" in s or "65+" in s or "65 +" in s:
        return "65+"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_education(x):
    s = clean_text(x).lower()

    if "primary" in s:
        return "Primary education"
    if "secondary" in s or "vocational" in s:
        return "Secondary / vocational education"
    if "bachelor" in s or "master" in s:
        return "Higher education"
    if "phd" in s or "postdoctoral" in s:
        return "Doctorate / PhD"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_income(x):
    s = clean_text(x).lower()

    if "much below" in s:
        return "Well below median"
    if "somewhat below" in s:
        return "Slightly below median"
    if "around median" in s:
        return "Around median"
    if "somewhat above" in s:
        return "Slightly above median"
    if "much above" in s:
        return "Well above median"
    if s in {"", "nan"}:
        return np.nan
    return "Other"

df = pd.read_csv(INPUT)
df.columns = df.columns.str.strip()

# -----------------------------
# 1) Demographics
# -----------------------------
df["city"] = "Bergen"

gender_col = "5.2 What is your gender?"
age_col = "5.3 What age are you?"
education_col = "5.4 What is your highest level of education that you have completed?"
income_col = "5.5 The median income for households in Norway was about 800 000 NOK before tax, or 630 000 NOK after in 2023.Would you say your household income is"

# Keep raw demographic values for QA
df["gender_raw"] = df[gender_col].map(clean_text) if gender_col in df.columns else pd.NA
df["age_raw"] = df[age_col].map(clean_text) if age_col in df.columns else pd.NA
df["education_raw"] = df[education_col].map(clean_text) if education_col in df.columns else pd.NA
df["income_raw"] = df[income_col].map(clean_text) if income_col in df.columns else pd.NA

# Harmonized demographic categories for cross-city reporting
df["gender"] = df["gender_raw"].map(harmonize_gender)
df["age"] = df["age_raw"].map(harmonize_age)
df["education"] = df["education_raw"].map(harmonize_education)
df["income"] = df["income_raw"].map(harmonize_income)

postal_col = "5.1 Fill in postal code"
if postal_col in df.columns:
    df["postal_code"] = df[postal_col].astype(str).str.extract(r"(\d{4})", expand=False)
else:
    df["postal_code"] = pd.NA

# -----------------------------
# 2) Borrowed from sharing station
# -----------------------------
borrowed_col = "3.1 Have you ever borrowed an item from a sharing station?"
df["borrowed_sharing_station"] = normalize_yes_no_series(df[borrowed_col]) if borrowed_col in df.columns else pd.NA

# -----------------------------
# 3) Initiatives funnel columns (Know_/Use_ already created in preprocessing)
# -----------------------------
initiative_map = [
    ("Know_second_hand", "know__secondhand"),
    ("Use_second_hand",  "use__secondhand"),
    ("Know_sharing",     "know__sharing"),
    ("Use_sharing",      "use__sharing"),
    ("Know_renting",     "know__renting"),
    ("Use_renting",      "use__renting"),
    ("Know_repair",      "know__repair"),
    ("Use_repair",       "use__repair"),
]
for src, dst in initiative_map:
    df[dst] = pd.to_numeric(df[src], errors="coerce") if src in df.columns else pd.NA

# -----------------------------
# 4) Items mapping (Bergen processed columns)
#    Pressure washer needs combining: Own_Jet washer + Own_High pressure washer
# -----------------------------
own_candidates = [c for c in ["Own_Jet washer", "Own_High pressure washer"] if c in df.columns]
rent_candidates = [c for c in ["Rent_Jet washer", "Rent_High pressure washer"] if c in df.columns]
df["Own_PressureWasher_combined"] = df[own_candidates].fillna(0).max(axis=1) if own_candidates else 0
df["Rent_PressureWasher_combined"] = df[rent_candidates].fillna(0).max(axis=1) if rent_candidates else 0

ITEMS = {
    "vacuum_cleaner":        {"own": "Own_Hoover", "use": "2.2 Hoover", "rent": "Rent_Hoover"},
    "steam_cleaner":         {"own": "Own_Steam cleaner", "use": "2.3 Steam cleaner", "rent": "Rent_Steam cleaner"},
    "drill":                 {"own": "Own_Drill", "use": "2.4 Drill", "rent": "Rent_Drill"},
    "video_projector":       {"own": "Own_Video projector", "use": "2.5 Video projector", "rent": "Rent_Video projector"},
    "hand_sander":           {"own": "Own_Hand sander", "use": "2.6 Hand sander", "rent": "Rent_Hand sander"},
    "fitness_equipment":     {"own": "Own_Fitness equipment", "use": "2.7 Fitness equipment", "rent": "Rent_Fitness equipment"},
    "football_basketball":   {"own": "Own_Football & basketball", "use": "2.8 Football & basketball", "rent": "Rent_Football & basketball"},
    "table_tennis":          {"own": "Own_Table tennis", "use": "2.9 Table tennis", "rent": "Rent_Table tennis"},
    "iron":                  {"own": "Own_Iron", "use": "2.10 Iron", "rent": "Rent_Iron"},
    "sewing_machine":        {"own": "Own_Sewing machine", "use": "2.11 Sewing machine", "rent": "Rent_Sewing machine"},
    "volleyball_set":        {"own": "Own_Volleyball & net", "use": "2.12 Volleyball & net", "rent": "Rent_Volleyball & net"},
    "foldable_chairs_table": {"own": "Own_Foldable chairs & table", "use": "2.13 Foldable chairs & table", "rent": "Rent_Foldable chairs & table"},
    "carpet_cleaner":        {"own": "Own_Carpet cleaner", "use": "2.14 Carpet cleaner", "rent": "Rent_Carpet cleaner"},
    "pressure_washer":       {"own": "Own_PressureWasher_combined", "use": "2.15 High pressure cleaner", "rent": "Rent_PressureWasher_combined"},
}

for slug, m in ITEMS.items():
    df[f"own__{slug}"] = pd.to_numeric(df[m["own"]], errors="coerce") if m["own"] in df.columns else pd.NA
    df[f"rent__{slug}"] = pd.to_numeric(df[m["rent"]], errors="coerce") if m["rent"] in df.columns else pd.NA
    df[f"usefreq__{slug}"] = map_freq_series(df[m["use"]]) if m["use"] in df.columns else np.nan



# -----------------------------
# 5) Underutilization flags + indices
# -----------------------------
under_cols = []
own_cols = []
for slug in ITEMS.keys():
    own = df[f"own__{slug}"]
    freq = df[f"usefreq__{slug}"]
    df[f"underutilized__{slug}"] = np.where(
        own == 1,
        np.where(pd.isna(freq), 1, np.where(freq <= 2, 1, 0)),
        np.nan
    )
    under_cols.append(f"underutilized__{slug}")
    own_cols.append(f"own__{slug}")

df["ownership_count"] = df[own_cols].fillna(0).sum(axis=1)
df["underutilization_count"] = df[under_cols].sum(axis=1)
df["underutilization_index"] = np.where(
    df["ownership_count"] > 0,
    df["underutilization_count"] / df["ownership_count"],
    np.nan
)

# -----------------------------
# 6) Borrowing reasons (if present as binary cols in processed)
# -----------------------------
YES_REASONS = [
    "To save money",
    "To have more goods available",
    "To play sports or relax",
    "To learn new things",
    "To create opportunities for myself",
    "To meet people",
    "To support local cooperation and community building",
    "To support equal access to goods for everyone",
    "To reduce consumption and/or support the environment",
]
NO_REASONS = [
    "Lack of sharing stations",
    "Lack of information on how sharing stations work",
    "Lack of information on offered products",
    "Lack of product availability",
    "Lack of quality and maintenance",
    "Lack of hygiene",
    "Time-consuming",
    "It is too complicated",
    "It is too expensive",
    "I am used to owning goods",
    "I use my items so often that I rather own them",
    "I dont trust sharing station providers",
    "I dont think it makes a difference for the environment",
]

def slugify_reason(r: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", r.lower()).strip("_")

for r in YES_REASONS:
    if r in df.columns:
        df[f"reason_yes__{slugify_reason(r)}"] = pd.to_numeric(df[r], errors="coerce")
for r in NO_REASONS:
    if r in df.columns:
        df[f"reason_no__{slugify_reason(r)}"] = pd.to_numeric(df[r], errors="coerce")

# -----------------------------
# 7) Qualitative categories
# -----------------------------
df["other_not_category"] = df["Other_NOT"].astype(str).map(clean_text) if "Other_NOT" in df.columns else ""
df["nevershare_category"] = df["NeverShare_Category"].astype(str).map(clean_text) if "NeverShare_Category" in df.columns else ""

# -----------------------------
# 8) Expected effects (Q4.13–Q4.17)
# -----------------------------
# These are Likert items (1–5) where:
# 1 = strongly decrease, 3 = neutral, 5 = strongly increase
EXPECTED_EFFECTS_MAP = {
    "4.13 The amount of jobs will…": "expect__jobs",
    "4.14 Household spending on goods will…": "expect__spending",
    "4.16 The amount of new businesses and profits will…": "expect__business",
    "4.16 The amount of sharing information through platforms / apps will…": "expect__platforms",
    "4.17 The negative environmental impact will…": "expect__neg_env_impact",
}

for src, dst in EXPECTED_EFFECTS_MAP.items():
    if src in df.columns:
        df[dst] = pd.to_numeric(df[src], errors="coerce")
    else:
        df[dst] = pd.NA


# -----------------------------
# Save
# -----------------------------
df.to_csv(OUTPUT, index=False)
print(f"Saved harmonized Bergen dataset to: {OUTPUT}")
