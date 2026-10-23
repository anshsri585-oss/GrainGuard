
import pandas as pd

# Read the hourly temperature history
df = pd.read_csv("temperature_history.csv")

# Select Stack S07, Probe P2
mask = (
    (df["stack_id"] == "S07") &
    (df["probe_id"] == "P2")
)

# Hourly readings of S07-P2 are in time order
indices = df[mask].index

# Introduce artificial heating from hour 8
for hour, idx in enumerate(indices):
    if hour >= 8:
        df.loc[idx, "temperature"] += (hour - 7) * 0.5

# Save separately so original data stays unchanged
df.to_csv("temperature_with_hotspot.csv", index=False)

# Display the affected probe readings
print(df[mask][["timestamp", "temperature"]])

print("Artificial hotspot simulation saved!")

print("\nHotspot readings for S07-P2:")

print(
    df[
        (df["stack_id"] == "S07") &
        (df["probe_id"] == "P2")
    ][["timestamp", "temperature"]].to_string(index=False)
)