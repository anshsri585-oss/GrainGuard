from pathlib import Path
from datetime import datetime
import json
import csv
import paho.mqtt.client as mqtt

BASE_DIR = Path(__file__).resolve().parent

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "grainguard/demo/s01/ambient"

FILE = BASE_DIR / "mqtt_readings.csv"

# Create CSV with headings if it doesn't exist
if not FILE.exists():
    with open(FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "stack_id",
            "sensor_type",
            "temperature_c",
            "humidity_pct",
            "data_source"
        ])

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to HiveMQ!")
        client.subscribe(TOPIC, qos=0)
        print("Subscribed to:", TOPIC)
    else:
        print("Connection failed with reason code:", reason_code)

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode("utf-8"))

        timestamp = datetime.now().isoformat(timespec="seconds")

        # Robust type conversion
        temp_val = float(data["temperature_c"])
        rh_val = float(data["humidity_pct"])

        row = [
            timestamp,
            str(data["stack_id"]),
            str(data["sensor_type"]),
            temp_val,
            rh_val,
            str(data.get("data_source", "WOKWI_SIMULATION"))
        ]

        with open(FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print(f"[{timestamp}] Saved reading for {data['stack_id']}: {temp_val}°C, {rh_val}% RH")

    except (ValueError, KeyError) as e:
        print("Invalid message payload:", e)

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT broker ({BROKER}:{PORT})...")
client.connect(BROKER, PORT, keepalive=60)

print(f"Listening for readings on topic '{TOPIC}'. Press Ctrl+C to exit.")
client.loop_forever()
