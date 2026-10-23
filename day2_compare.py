
import pandas as pd

# Load our hotspot dataset
df = pd.read_csv("temperature_with_hotspot.csv")

# Convert timestamp column to datetime
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Select Stack S07, Probe P2
hotspot = df[
    (df["stack_id"] == "S07") &
    (df["probe_id"] == "P2")
].copy()

# 1-hour monitoring: all available readings
hourly = hotspot.copy()

# 4-hour monitoring: 00, 04, 08, 12, 16, 20
four_hourly = hotspot[
    hotspot["timestamp"].dt.hour % 4 == 0
].copy()

print("\n1-HOUR MONITORING")
print(hourly[["timestamp", "temperature"]].to_string(index=False))

print("\n4-HOUR MONITORING")
print(four_hourly[["timestamp", "temperature"]].to_string(index=False))

print("\nTotal 1-hour readings:", len(hourly))
print("Total 4-hour readings:", len(four_hourly))

four_hourly.to_csv("four_hour_readings.csv", index=False)


# Example alert threshold
threshold = 30

# Find readings crossing the threshold
alert_hourly = hourly[
    hourly["temperature"] >= threshold
]

alert_four_hourly = four_hourly[
    four_hourly["temperature"] >= threshold
]

# Get first alert time
if not alert_hourly.empty:
    time_1h = alert_hourly.iloc[0]["timestamp"]
    print("1-hour first alert:", time_1h)
else:
    print("No alert in 1-hour monitoring")

if not alert_four_hourly.empty:
    time_4h = alert_four_hourly.iloc[0]["timestamp"]
    print("4-hour first alert:", time_4h)
else:
    print("No alert in 4-hour monitoring")

# Compare detection delay
if not alert_hourly.empty and not alert_four_hourly.empty:
    delay = (time_4h - time_1h).total_seconds() / 3600
    print("Extra detection delay:", delay, "hours")
