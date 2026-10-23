import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

rng = np.random.default_rng(42)

records = []

# 200 independently generated synthetic scenarios
N_SCENARIOS = 200
HOURS = 120

for scenario in range(N_SCENARIOS):

    # Some scenarios contain a hotspot event
    has_hotspot = scenario % 2 == 0

    base_temp = rng.uniform(24, 30)

    # A gradual warning trend develops 24 hours prior to onset
    if has_hotspot:
        onset_hour = int(rng.integers(60, 96))
        early_start = onset_hour - 24
        heating_strength = rng.uniform(0.06, 0.15)
    else:
        onset_hour = None

    for hour in range(HOURS):

        daily = 0.6 * np.sin(2 * np.pi * hour / 24)
        noise = rng.normal(0, 0.15)

        temperature = base_temp + daily + noise

        if has_hotspot:
            if hour >= early_start:
                temperature += (
                    hour - early_start
                ) * heating_strength

        records.append({
            "scenario_id": scenario,
            "hour": hour,
            "temperature_c": round(temperature, 3),
            "hotspot_onset_hour": onset_hour,
            "data_source": "SYNTHETIC"
        })

df = pd.DataFrame(records)

output_dir = BASE_DIR / "data" / "synthetic"
output_dir.mkdir(
    parents=True,
    exist_ok=True
)

output_file = output_dir / "ml_scenarios.csv"
df.to_csv(
    output_file,
    index=False
)

print("Total rows:", len(df))
print("Number of scenarios:", df["scenario_id"].nunique())
print(f"Synthetic ML scenarios saved to {output_file}!")
