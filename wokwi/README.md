# Wokwi ESP32 + DHT22 MQTT Simulation Guide

This folder contains the ready-to-run ESP32 + DHT22 firmware simulation for demonstrating GrainGuard's IoT ambient telemetry pipeline.

## How to Run the Wokwi Simulation

1. Open [https://wokwi.com](https://wokwi.com) in your web browser.
2. Select **ESP32** -> **Start from Scratch** (or create a new project).
3. Paste the contents of `wokwi_esp32_dht22.ino` into the code editor (`sketch.ino`).
4. Click on the **diagram.json** tab (or add components manually: ESP32 + DHT22 on Pin 15) and paste `diagram.json`.
5. Under the Library Manager tab in Wokwi, add:
   - `PubSubClient`
   - `DHT sensor library for ESPx` (or `DHTesp`)
   - `ArduinoJson`
6. Click the green **Play (Start Simulation)** button.

## How to Ingest Data in GrainGuard

1. Open a terminal on your computer and run:
   ```bash
   python mqtt_receiver.py
   ```
2. You will see:
   ```text
   Connected to HiveMQ!
   Subscribed to: grainguard/demo/s01/ambient
   [2026-10-20T20:25:00] Saved reading for S01: 28.5°C, 54.0% RH
   ```
3. Open or refresh your Streamlit dashboard (`streamlit run dashboard.py`).
4. The **MQTT Ambient Sensor Telemetry** section will immediately show the live ambient temperature and humidity readings recorded from Wokwi!
