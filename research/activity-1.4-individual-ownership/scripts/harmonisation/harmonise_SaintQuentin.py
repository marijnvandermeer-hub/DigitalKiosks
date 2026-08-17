import os
import re
import pandas as pd
import numpy as np

INPUT = "data/processed/survey_data/survey_Saint_Quetin_processed.csv"
OUTPUT = "data/processed/survey_data/harmonized/SaintQuentin_survey_harmonized.csv"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

FREQ_MAP = {
    "day": 5, "every day": 5, "everyday": 5,
    "week": 4, "every week": 4,
    "month": 3, "every month": 3,
    "less": 2, "less often": 2,
    "never": 1,
    # if translation produced other labels
    "very often": 5,
    "often": 4,
    "sometimes": 3,
    "rarely": 2,
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
    # avoid pandas FutureWarning
    t = t.replace(FREQ_MAP)
    return pd.to_numeric(t, errors="coerce")

def normalize_yes_no_series(s: pd.Series) -> pd.Series:
    t = s.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    return t.map(YESNO)

def to_binary(series: pd.Series) -> pd.Series:
    """
    Robust conversion to 0/1:
    - Accepts 1/0, True/False, Yes/No, y/n
    - Anything else -> NA
    """
    s = series.copy()
    num = pd.to_numeric(s, errors="coerce")
    if num.notna().any():
        return num.where(num.isin([0, 1]), np.nan)

    t = s.astype(str).str.strip().str.lower().replace({"nan": np.nan, "": np.nan})
    mapping = {"1": 1, "0": 0, "true": 1, "false": 0, "yes": 1, "no": 0, "y": 1, "n": 0}
    return t.map(mapping)

def slugify_reason(text: str) -> str:
    # match Bergen harmonized naming style: lower, non-alnum -> _, trim underscores
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def harmonize_gender(x):
    s = clean_text(x).lower()
    if s in {"women", "woman", "female"}:
        return "Woman"
    if s in {"man", "men", "male"}:
        return "Man"
    if "prefer not" in s:
        return "Prefer not to say"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_age(x):
    s = clean_text(x).lower()
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
    if "over 65" in s or "65+" in s:
        return "65+"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_education(x):
    s = clean_text(x).lower()

    if "niveau 1" in s or "école primaire" in s or "ecole primaire" in s:
        return "Primary education"
    if "niveau 2" in s or "niveau 3" in s or "collège" in s or "college" in s or "cap" in s or "bep" in s:
        return "Secondary / vocational education"
    if "niveau 4" in s or "baccalaur" in s:
        return "Higher education"
    if "niveau 5" in s or "bac +2" in s or "licence" in s or "master" in s:
        return "Higher education"
    if "niveau 6" in s or "doctorat" in s or "post-doctorat" in s:
        return "Doctorate / PhD"
    if s in {"", "nan"}:
        return np.nan
    return "Other"


def harmonize_income(x):
    s = clean_text(x).lower()

    if "well below" in s:
        return "Well below median"
    if "slightly lower" in s:
        return "Slightly below median"
    if "around" in s:
        return "Around median"
    if "slightly higher" in s:
        return "Slightly above median"
    if "well above" in s:
        return "Well above median"
    if s in {"", "nan"}:
        return np.nan
    return "Other"

df = pd.read_csv(INPUT)
df.columns = df.columns.str.strip()

# -----------------------------
# 1) Demographics
# -----------------------------
df["city"] = "SaintQuentin"
df["gender_raw"] = df["What is your gender?"].map(clean_text) if "What is your gender?" in df.columns else pd.NA
df["age_raw"] = df["How old are you?"].map(clean_text) if "How old are you?" in df.columns else pd.NA
df["education_raw"] = df["What is the highest level of education you have completed?"].map(clean_text) if "What is the highest level of education you have completed?" in df.columns else pd.NA
df["income_raw"] = df["Would you say your household income is"].map(clean_text) if "Would you say your household income is" in df.columns else pd.NA

df["gender"] = df["gender_raw"].map(harmonize_gender)
df["age"] = df["age_raw"].map(harmonize_age)
df["education"] = df["education_raw"].map(harmonize_education)
df["income"] = df["income_raw"].map(harmonize_income)

postal_candidates = [
    "Enter your postal code",
    "Enter your postal code with 2100",
    "Postal code",
    "postal code",
]
postal_src = next((c for c in postal_candidates if c in df.columns), None)
df["postal_code"] = df[postal_src].astype(str).str.extract(r"(\d{4,5})", expand=False) if postal_src else pd.NA

borrowed_col = "Have you ever borrowed an item from a sharing station?"
df["borrowed_sharing_station"] = normalize_yes_no_series(df[borrowed_col]) if borrowed_col in df.columns else pd.NA

# -----------------------------
# 2) Initiatives funnel columns (SQ headers: know without .1, use with .1)
# -----------------------------
SQ_INITIATIVE_COLS = {
    "secondhand": (
        "Second-hand shops [Friphipster, Ding Fring, Emmaus]",
        "Second-hand shops [Friphipster, Ding Fring, Emmaus].1",
    ),
    "sharing": (
        "Sharing initiatives [Place des Services, Public Library, Book box]",
        "Sharing initiatives [Place des Services, Public Library, Book box].1",
    ),
    "renting": (
        "Rental initiatives [Electric bike rental, AlloVoisins, Kiwiiz]",
        "Rental initiatives [Electric bike rental, AlloVoisins, Kiwiiz].1",
    ),
    "repair": (
        "Repair workshops [Mary Cycles, BricolcafÃ©]",
        "Repair workshops [Mary Cycles, BricolcafÃ©].1",
    ),
}

for key, (know_src, use_src) in SQ_INITIATIVE_COLS.items():
    know_col = know_src if know_src in df.columns else None
    use_col = use_src if use_src in df.columns else None

    if know_col is None:
        candidates = [c for c in df.columns if c.startswith(know_src.split("[")[0].strip()) and not c.endswith(".1")]
        know_col = candidates[0] if candidates else None

    if use_col is None:
        candidates = [c for c in df.columns if c.startswith(use_src.split("[")[0].strip()) and c.endswith(".1")]
        use_col = candidates[0] if candidates else None

    df[f"know__{key}"] = to_binary(df[know_col]) if know_col else pd.NA
    df[f"use__{key}"] = to_binary(df[use_col]) if use_col else pd.NA

# -----------------------------
# 3) Items mapping
# -----------------------------
ITEMS = {
    "vacuum_cleaner":      {"own": "Do you own a vacuum cleaner?", "use": "How often do you use this vacuum cleaner?", "rent": "Would you consider borrowing a vacuum cleaner?"},
    "steam_cleaner":       {"own": "Do you own a steam cleaner?", "use": "How often do you use this steam cleaner?", "rent": "Would you consider borrowing a steam cleaner?"},
    "pressure_washer":     {"own": "Do you own a pressure washer?", "use": "How often do you use this pressure washer?", "rent": "Would you consider borrowing a pressure washer?"},
    "carpet_cleaner":      {"own": "Do you own a carpet shampoo machine?", "use": "How often do you use this carpet shampoo machine?", "rent": "Would you consider borrowing a carpet shampoo machine?"},
    "drill":               {"own": "Do you own a drill?", "use": "How often do you use this drill?", "rent": "Would you consider borrowing a drill?"},
    "hand_sander":         {"own": "Do you own a hand sander?", "use": "How often do you use this hand sander?", "rent": "Would you consider borrowing a hand sander?"},
    "fitness_equipment":   {"own": "Do you own one or more fitness devices?", "use": "How often do you use these fitness devices?", "rent": "Would you consider borrowing fitness devices?"},
    "table_tennis":        {"own": "Do you own table tennis paddles?", "use": "How often do you use these paddles?", "rent": "Would you consider borrowing table tennis paddles?"},
    "football_basketball": {"own": "Do you own a football or basketball?", "use": "How often do you use this football or basketball?", "rent": "Would you consider borrowing a football or basketball?"},
    "volleyball_set":      {"own": "Do you own a beach volleyball set?", "use": "How often do you use this beach volleyball set?", "rent": "Would you consider borrowing a beach volleyball set?"},
}

for slug, m in ITEMS.items():
    df[f"own__{slug}"] = pd.to_numeric(df[m["own"]], errors="coerce") if m["own"] in df.columns else pd.NA
    df[f"rent__{slug}"] = pd.to_numeric(df[m["rent"]], errors="coerce") if m["rent"] in df.columns else pd.NA
    df[f"usefreq__{slug}"] = map_freq_series(df[m["use"]]) if m["use"] in df.columns else np.nan

# -----------------------------
# 4) Underutilization flags + indices
# -----------------------------
under_cols, own_cols = [], []
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
# 5) Borrowing reasons -> harmonized binary columns
# We try BOTH:
#   - existing binary columns (like Bergen: "To save money")
#   - or a multi-select text column "3.2 ..." / "3.3 ..." that contains semicolon-separated reasons
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

# candidate source columns (some processed files use single multi-select text columns)
COL_BORROW_TEXT_CANDIDATES = [
    "3.2 What is/are your main reason(s) to borrow an item from a sharing station?",
    "What is/are your main reason(s) to borrow an item from a sharing station?",
]
COL_NOT_TEXT_CANDIDATES = [
    "3.3 What is/are your main reason(s) to not borrow an item from a sharing station?",
    "What is/are your main reason(s) to not borrow an item from a sharing station?",
]

col_borrow_txt = next((c for c in COL_BORROW_TEXT_CANDIDATES if c in df.columns), None)
col_not_txt = next((c for c in COL_NOT_TEXT_CANDIDATES if c in df.columns), None)

def contains_reason(series: pd.Series, reason: str) -> pd.Series:
    # works for semicolon-separated or any free text; case-insensitive
    pat = re.escape(reason.lower())
    t = series.astype(str).str.lower().replace({"nan": "", "": ""})
    return t.str.contains(pat, regex=True)

# YES reasons
for r in YES_REASONS:
    out_col = f"reason_yes__{slugify_reason(r)}"

    if r in df.columns:
        # already binary
        df[out_col] = pd.to_numeric(df[r], errors="coerce")
    elif col_borrow_txt:
        df[out_col] = np.where(contains_reason(df[col_borrow_txt], r), 1, 0)
    else:
        df[out_col] = pd.NA

# NO reasons
for r in NO_REASONS:
    out_col = f"reason_no__{slugify_reason(r)}"

    if r in df.columns:
        df[out_col] = pd.to_numeric(df[r], errors="coerce")
    elif col_not_txt:
        df[out_col] = np.where(contains_reason(df[col_not_txt], r), 1, 0)
    else:
        df[out_col] = pd.NA

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
    "The number of jobs": "expect__jobs",
    "Household spending on goods": "expect__spending",
    "Income of new businesses and profits": "expect__business",
    "The amount of information shared by platforms / apps": "expect__platforms",
    "Negative impact on the environment": "expect__neg_env_impact",
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
print(f"Saved harmonized SaintQuentin dataset to: {OUTPUT}")

# Optional quick sanity check prints:
print("\nSanity check initiative non-null rates:")
for k in ["secondhand", "sharing", "renting", "repair"]:
    kc, uc = f"know__{k}", f"use__{k}"
    if kc in df.columns and uc in df.columns:
        print(k, "know non-null:", int(df[kc].notna().sum()), "use non-null:", int(df[uc].notna().sum()))

print("\nSanity check reason cols (non-null):")
ry = [c for c in df.columns if c.startswith("reason_yes__")]
rn = [c for c in df.columns if c.startswith("reason_no__")]
print("reason_yes__ cols:", len(ry), "non-null cells:", int(df[ry].notna().sum().sum()) if ry else 0)
print("reason_no__ cols:", len(rn), "non-null cells:", int(df[rn].notna().sum().sum()) if rn else 0)
