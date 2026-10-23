from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import classification_report, confusion_matrix
import joblib

BASE_DIR = Path(__file__).resolve().parent

# 1. Load synthetic scenarios
data_file = BASE_DIR / "data" / "synthetic" / "ml_scenarios.csv"
df = pd.read_csv(data_file)

df = df.sort_values(["scenario_id", "hour"])

# 2. Create features using PAST readings only
g = df.groupby("scenario_id")["temperature_c"]

df["current_temp"] = df["temperature_c"]

df["avg_temp_24h"] = g.transform(
    lambda x: x.rolling(24, min_periods=24).mean()
)

df["max_temp_24h"] = g.transform(
    lambda x: x.rolling(24, min_periods=24).max()
)

df["temp_change_6h"] = g.diff(6)
df["temp_change_24h"] = g.diff(24)

# 3. Future event target: hotspot will begin in next 24 hours
onset = df["hotspot_onset_hour"]

df["future_hotspot"] = (
    onset.notna()
    & (onset > df["hour"])
    & (onset <= df["hour"] + 24)
).astype(int)

# Keep only readings BEFORE any event onset
# (Model is strictly designed to predict future onset, not active mature hotspots)
df = df[
    onset.isna() | (df["hour"] < onset)
].copy()

features = [
    "current_temp",
    "avg_temp_24h",
    "max_temp_24h",
    "temp_change_6h",
    "temp_change_24h"
]

# First 24 hours don't have complete history
df = df.dropna(subset=features)

X = df[features]
y = df["future_hotspot"]
groups = df["scenario_id"]

# 4. Split by SCENARIO, not random rows (avoids intra-scenario data leakage)
splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.25,
    random_state=42
)

train_idx, test_idx = next(
    splitter.split(X, y, groups)
)

X_train = X.iloc[train_idx]
X_test = X.iloc[test_idx]
y_train = y.iloc[train_idx]
y_test = y.iloc[test_idx]

# 5. Train Random Forest
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
    min_samples_leaf=5
)

model.fit(X_train, y_train)

# 6. Evaluate on held-out scenarios
predictions = model.predict(X_test)

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))
print("Training scenarios:",
      groups.iloc[train_idx].nunique())
print("Testing scenarios:",
      groups.iloc[test_idx].nunique())

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions, labels=[0, 1]))

print("\nClassification Report:")
print(classification_report(
    y_test, predictions, labels=[0, 1],
    zero_division=0
))

# 7. Save model and feature names
models_dir = BASE_DIR / "models"
models_dir.mkdir(parents=True, exist_ok=True)

model_path = models_dir / "hotspot_model.joblib"
joblib.dump(
    {"model": model, "features": features},
    model_path
)

print(f"\nModel saved successfully to {model_path}!")
