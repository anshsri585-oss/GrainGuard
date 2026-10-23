

import random
import pandas as pd

readings = []

for stack in range(1, 17):

    for probe in range(1, 4):

        temperature = round(
            random.uniform(25, 30), 2
        )

        reading = {
            "stack_id": f"S{stack:02d}",
            "probe_id": f"P{probe}",
            "temperature": temperature
        }

        readings.append(reading)

df = pd.DataFrame(readings)

print(df)

df.to_csv("temperature_readings.csv", index=False)

print("Temperature readings saved successfully!")
