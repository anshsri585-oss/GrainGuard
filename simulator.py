import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Same random results every time (repeatable simulation)
rng = np.random.default_rng(42)

readings = []

# 30 days of hourly readings to start
timestamps = pd.date_range(
    start="2026-09-01",
    periods=30 * 24,
    freq="h"
)

# 16 stacks, 3 measuring points per stack (upper, middle, lower)
positions = ["upper", "middle", "lower"]

for stack in range(1, 17):

    # Different starting baseline temperature for every stack (25 to 29 °C)
    base_temp = rng.uniform(25, 29)

    # Small natural physical differences between probe locations
    probe_offsets = rng.normal(0, 0.25, size=3)

    for hour, timestamp in enumerate(timestamps):

        # Daily sinusoidal temperature fluctuation (diurnal cycle)
        daily_change = 0.7 * np.sin(
            2 * np.pi * hour / 24
        )

        # Slow synoptic/weekly background variation
        slow_change = 0.3 * np.sin(
            2 * np.pi * hour / (24 * 7)
        )

        for probe_index, position in enumerate(positions):

            temperature = (
                base_temp
                + daily_change
                + slow_change
                + probe_offsets[probe_index]
                + rng.normal(0, 0.15)
            )

            # Simulated hotspot: Stack 7, middle position (P2)
            if stack == 7 and position == "middle":
                if hour >= 180:
                    temperature += min(
                        (hour - 180) * 0.025, 7
                    )

            # Simulated hotspot: Stack 12, lower position (P3)
            if stack == 12 and position == "lower":
                if hour >= 350:
                    temperature += min(
                        (hour - 350) * 0.018, 5
                    )

            # Simulated hotspot: Stack 4, upper position (P1)
            if stack == 4 and position == "upper":
                if hour >= 480:
                    temperature += min(
                        (hour - 480) * 0.02, 4
                    )

            readings.append({
                "timestamp": timestamp,
                "stack_id": f"S{stack:02d}",
                "probe_id": f"P{probe_index + 1}",
                "position": position,
                "temperature_c": round(temperature, 2),
                "data_source": "SYNTHETIC"
            })

# Convert to DataFrame
df = pd.DataFrame(readings)

# Create folder for simulated data
output_dir = BASE_DIR / "data" / "synthetic"
output_dir.mkdir(
    parents=True,
    exist_ok=True
)

# Save simulation
output_file = output_dir / "sensor_data.csv"
df.to_csv(
    output_file,
    index=False
)

print(df.head())
print("\nTotal readings:", len(df))
print("Number of stacks:", df["stack_id"].nunique())
print(f"Simulation saved successfully to {output_file}!")
