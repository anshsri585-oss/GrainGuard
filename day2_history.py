
import random
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)

readings = []

start_time = datetime(2026, 10, 19, 0, 0)

for stack in range(1, 17):

    for probe in range(1, 4):

        # Starting temperature
        temperature = random.uniform(25, 29)

        for hour in range(24):

            # Generate timestamp
            timestamp = start_time + timedelta(hours=hour)

            # Small change in previous temperature
            temperature += random.uniform(-0.2, 0.2)

            readings.append({
                "timestamp": timestamp,
                "stack_id": f"S{stack:02d}",
                "probe_id": f"P{probe}",
                "temperature": round(temperature, 2),
                "data_source": "SYNTHETIC"
            })

df = pd.DataFrame(readings)

df.to_csv("temperature_history.csv", index=False)

print(df.head(10))
print("Total readings:", len(df))
print("Temperature history saved successfully!")
