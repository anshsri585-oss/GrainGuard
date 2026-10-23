
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("temperature_with_hotspot.csv")

df["timestamp"] = pd.to_datetime(df["timestamp"])

# Select Stack S07
stack = df[df["stack_id"] == "S07"]

# Draw graph for all three probes
for probe in ["P1", "P2", "P3"]:

    data = stack[stack["probe_id"] == probe]

    plt.plot(
        data["timestamp"],
        data["temperature"],
        marker="o",
        label=probe
    )

plt.axhline(
    y=30,
    linestyle="--",
    label="Example alert threshold"
)

plt.xlabel("Time")
plt.ylabel("Temperature (°C)")
plt.title("Stack S07 - Temperature Monitoring")

plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.tight_layout()

plt.show()
