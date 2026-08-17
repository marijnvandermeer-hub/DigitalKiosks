import os
import re
import pandas as pd
import numpy as np

INPUT = "data/processed/survey_data/Survey_Familjebostader_mvdm_processed.csv"
OUTPUT = "data/processed/survey_data/harmonized/Gothenburg_survey_harmonized.csv"
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

def map_freq_series(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    return pd.to_numeric(t.replace(FREQ_MAP), errors="coerce")

def normalize_yes_no_series(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    return t.map(YESNO)

def harmonize_gender(x):
    s = clean_text(x).lower()
    if s == "female":
        return "Woman"
    if s == "male":
        return "Man"
    if s == "other":
        return "Other"
    if "prefer" in s or "prefere" in s:
        return "Prefer not to say"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_age(x):
    s = clean_text(x).lower()
    s = s.replace("years", "").replace("year", "").strip()

    if s == "18-25":
        return "18–25"
    if s == "25-35":
        return "26–35"
    if s == "35-45":
        return "36–45"
    if s == "45-55":
        return "46–55"
    if s == "55-65":
        return "56–65"
    if "over 65" in s or "65+" in s:
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

    if "very under" in s:
        return "Well below median"
    if "somewhat under" in s:
        return "Slightly below median"
    if "around median" in s:
        return "Around median"
    if "somewhat over" in s:
        return "Slightly above median"
    if "very over" in s:
        return "Well above median"
    if s in {"", "nan"}:
        return np.nan
    return "Other"

df = pd.read_csv(INPUT)
df.columns = df.columns.str.strip()

# -----------------------------
# 1) Demographics
# -----------------------------
df["city"] = "Gothenburg"

gender_col = "Gender"
age_col = "Age"
education_col = "Education"
income_col = "Would you say your household income is"

df["gender_raw"] = df[gender_col].map(clean_text) if gender_col in df.columns else pd.NA
df["age_raw"] = df[age_col].map(clean_text) if age_col in df.columns else pd.NA
df["education_raw"] = df[education_col].map(clean_text) if education_col in df.columns else pd.NA
df["income_raw"] = df[income_col].map(clean_text) if income_col in df.columns else pd.NA

df["gender"] = df["gender_raw"].map(harmonize_gender)
df["age"] = df["age_raw"].map(harmonize_age)
df["education"] = df["education_raw"].map(harmonize_education)
df["income"] = df["income_raw"].map(harmonize_income)

postal_col = "postal code"
df["postal_code"] = df[postal_col].astype(str).str.extract(r"(\d{5})", expand=False) if postal_col in df.columns else pd.NA

# Optional: area if you created it in preprocessing
df["area"] = df["area"].astype(str).str.strip() if "area" in df.columns else pd.NA

# Borrowed from sharing station question (if present)
borrowed_col = "Have you ever borrowed an item from a sharing station?"
df["borrowed_sharing_station"] = normalize_yes_no_series(df[borrowed_col]) if borrowed_col in df.columns else pd.NA

# -----------------------------
# 2) Initiatives funnel columns (already binary in preprocessing)
# -----------------------------
initiative_map = [
    ("Do you know initiatives second-hand shops", "know__secondhand"),
    ("Do you use them in your daily lives second-hand shops", "use__secondhand"),
    ("Do you know initiatives sharing initiatives", "know__sharing"),
    ("Do you use them in your daily lives sharing initiatives", "use__sharing"),
    ("Do you know initiatives renting initiatives", "know__renting"),
    ("Do you use them in your daily lives renting initiatives", "use__renting"),
    ("Do you know initiatives repair shops", "know__repair"),
    ("Do you use them in your daily lives repair shops", "use__repair"),
]
for src, dst in initiative_map:
    df[dst] = pd.to_numeric(df[src], errors="coerce") if src in df.columns else pd.NA

# -----------------------------
# 3) Items mapping (Gothenburg processed columns)
# -----------------------------
ITEMS = {
    "vacuum_cleaner":      {"own": "Own_Hoover", "use": "Hoover", "rent": "Borrow_Hoover"},
    "steam_cleaner":       {"own": "Own_Steam cleaner", "use": "Steam cleaner", "rent": "Borrow_Steam cleaner"},
    "drill":               {"own": "Own_Drill", "use": "Drill", "rent": "Borrow_Drill"},
    "video_projector":     {"own": "Own_Video projector", "use": "Video projector", "rent": "Borrow_Video projector"},
    "hand_sander":         {"own": "Own_Hand sander", "use": "Hand sander", "rent": "Borrow_Hand sander"},
    "fitness_equipment":   {"own": "Own_Fitness equipment", "use": "Fitness equipment", "rent": "Borrow_Fitness equipment"},
    "football_basketball": {"own": "Own_Football & basketball", "use": "Football & basketball", "rent": "Borrow_Football & basketball"},
    "table_tennis":        {"own": "Own_Table tennis", "use": "Table tennis", "rent": "Borrow_Table tennis"},
    "iron":                {"own": "Own_Iron", "use": "Iron", "rent": "Borrow_Iron"},
    "sewing_machine":      {"own": "Own_Sewing machine", "use": "Sewing machine", "rent": "Borrow_Sewing machine"},
}

for slug, m in ITEMS.items():
    df[f"own__{slug}"] = pd.to_numeric(df[m["own"]], errors="coerce") if m["own"] in df.columns else pd.NA
    df[f"rent__{slug}"] = pd.to_numeric(df[m["rent"]], errors="coerce") if m["rent"] in df.columns else pd.NA
    df[f"usefreq__{slug}"] = map_freq_series(df[m["use"]]) if m["use"] in df.columns else np.nan

# -----------------------------
# 4) Underutilization flags + indices
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
# 5) Borrow reasons binaries (from preprocessing if present)
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
# 6) Qualitative categories
# -----------------------------
df["other_not_category"] = df["Other_NOT"].astype(str).map(clean_text) if "Other_NOT" in df.columns else ""
df["nevershare_category"] = df["NeverShare_Category"].astype(str).map(clean_text) if "NeverShare_Category" in df.columns else ""

# -----------------------------
# 7) Expected effects (Q4.13–Q4.17)
# -----------------------------
# These are Likert items (1–5) where:
# 1 = strongly decrease, 3 = neutral, 5 = strongly increase
EXPECTED_EFFECTS_MAP = {
    "The amount of jobs will": "expect__jobs",
    "Household spending on goods will": "expect__spending",
    "The amount of new businesses and profits will": "expect__business",
    "The amount of shaveing information through platforms / apps will": "expect__platforms",
    "The negative environmental impact will": "expect__neg_env_impact",
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
print(f"Saved harmonized Gothenburg dataset to: {OUTPUT}")
