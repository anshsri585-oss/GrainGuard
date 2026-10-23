import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Load real USDA research datasets
environment = pd.read_csv(
    BASE_DIR / "data" / "real" / "grainguard_usda_daily_environment.csv"
)

outcomes = pd.read_csv(
    BASE_DIR / "data" / "real" / "grainguard_usda_sample_outcomes.csv"
)

# Deduplicate raw daily environment records if duplicate observations exist
initial_count = len(environment)
environment = environment.drop_duplicates()
dropped = initial_count - len(environment)
if dropped > 0:
    print(f"Removed {dropped} duplicate rows from environment data.")

# Summarize environmental observations per experiment replicate
features = environment.groupby(
    "experiment_id"
).agg(
    avg_temperature=("temperature_c", "mean"),
    max_temperature=("temperature_c", "max"),
    avg_humidity=("relative_humidity_pct", "mean"),
    max_humidity=("relative_humidity_pct", "max")
).reset_index()

# Join with recorded grain/insect outcomes
ml_data = features.merge(
    outcomes,
    on="experiment_id",
    how="inner"
)

(BASE_DIR / "data" / "processed").mkdir(
    parents=True,
    exist_ok=True
)

ml_data.to_csv(
    BASE_DIR / "data" / "processed" / "real_ml_data.csv",
    index=False
)

print("Dataset shape:", ml_data.shape)
print("Columns:", ml_data.columns.tolist())
print(ml_data.head())

print("\nMissing values:")
print(ml_data.isnull().sum())
