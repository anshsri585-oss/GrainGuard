from pathlib import Path
import pandas as pd
import joblib

BASE_DIR = Path(__file__).resolve().parent

# Load saved ML model
saved = joblib.load(BASE_DIR / "models" / "hotspot_model.joblib")
model = saved["model"]
features = saved["features"]

# Load existing simulated sensor readings
df = pd.read_csv(
    BASE_DIR / "data" / "synthetic" / "sensor_data.csv",
    parse_dates=["timestamp"]
)

# Sort chronologically for feature calculation and baseline tracking
df = df.sort_values(
    ["stack_id", "probe_id", "timestamp"]
)

# Compute initial baseline temperature (hour 0) BEFORE dropping rolling feature nulls
# This ensures consistency with dashboard.py
initial = (
    df.groupby(["stack_id", "probe_id"])
      .first()["temperature_c"]
      .rename("initial_temp")
      .reset_index()
)

g = df.groupby(
    ["stack_id", "probe_id"]
)["temperature_c"]

# Calculate features exactly as in training
df["current_temp"] = df["temperature_c"]

df["avg_temp_24h"] = g.transform(
    lambda x: x.rolling(24, min_periods=24).mean()
)

df["max_temp_24h"] = g.transform(
    lambda x: x.rolling(24, min_periods=24).max()
)

df["temp_change_6h"] = g.diff(6)
df["temp_change_24h"] = g.diff(24)

df = df.dropna(subset=features)

# Latest reading from each of the 48 probes
latest = df.groupby(
    ["stack_id", "probe_id"]
).tail(1).copy()

# ML prediction for each probe
latest["predicted_event_probability"] = (
    model.predict_proba(latest[features])[:, 1]
)

# Merge initial baseline computed from hour 0
latest = latest.merge(
    initial,
    on=["stack_id", "probe_id"]
)

latest["rise_c"] = (
    latest["temperature_c"] - latest["initial_temp"]
)

# Demo threshold - NOT validated spoilage limit
latest["heating_alert"] = latest["rise_c"] >= 2.0

# Save all individual probe results
latest.to_csv(
    BASE_DIR / "data" / "synthetic" / "probe_predictions.csv",
    index=False
)

# Combine three probes into one stack summary
summary = latest.groupby("stack_id").agg(
    current_temp=("temperature_c", "max"),
    max_rise_c=("rise_c", "max"),
    predicted_event_probability=(
        "predicted_event_probability", "max"
    ),
    heating_alert=("heating_alert", "any")
).reset_index()

summary["prediction_label"] = summary[
    "predicted_event_probability"
].apply(
    lambda p: "Synthetic Alert"
    if p >= 0.5 else "No Synthetic Alert"
)

summary.to_csv(
    BASE_DIR / "data" / "synthetic" / "latest_predictions.csv",
    index=False
)

print("\n16-STACK SUMMARY")
print(summary.to_string(index=False))

print("\nProbe predictions:", len(latest))
print("Stack summaries:", len(summary))
print("Predictions saved successfully!")
