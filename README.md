# GrainGuard
GrainGuard is an IoT-enabled grain-storage monitoring prototype. It combines simulated temperature probes, optional MQTT ambient telemetry, and an interpretable review workflow to help identify grain stacks that need physical inspection.

## Features
- Monitors 16 grain stacks through 48 simulated probe streams (upper, middle, and lower probes).
- Flags stacks when a probe's temperature rise from its own baseline reaches the review threshold.
- Provides a Streamlit dashboard with overview, stack history, inspections, sensor telemetry, analysis, and settings pages.
- Stores optional ESP32/DHT22 ambient readings received through MQTT.
- Produces hotspot-model predictions for all probe streams and stack-level summaries.
- Includes USDA-sample outcome data for the analysis page.

## Project structure

```text
project/
├── dashboard.py                 # Main Streamlit dashboard
├── simulator.py                 # Creates synthetic 48-probe readings
├── predict_hotspot.py           # Generates probe and stack predictions
├── mqtt_receiver.py             # Receives MQTT/Wokwi sensor messages
├── test_suite.py                # Automated verification checks
├── requirements.txt             # Python dependencies
├── data/
│   ├── synthetic/               # Sensor readings and predictions
│   ├── real/                    # USDA-sample datasets
│   └── processed/               # Prepared ML data
├── hotspot_model.joblib         # Trained hotspot model
└── wokwi/                       # ESP32 + DHT22 Wokwi simulation files
```

## Requirements

- Python 3.10 or later
- Internet access only for the optional public MQTT/Wokwi demonstration

## Installation

Open PowerShell in the project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```
## Run the dashboard

```powershell
streamlit run dashboard.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Regenerate the demonstration data

The project already contains data for the dashboard. To regenerate the synthetic sensor scenario and update predictions:

```powershell
python simulator.py
python predict_hotspot.py
```

Then return to the dashboard and select **Settings → Reload data**.

## Optional MQTT and Wokwi demonstration

The MQTT pipeline is optional. The dashboard continues to work with the supplied CSV data if no live MQTT connection is available.

1. Start the local receiver:

   ```powershell
   python mqtt_receiver.py
   ```

2. In Wokwi, create an ESP32 project and copy the contents of:

   - `wokwi/wokwi_esp32_dht22.ino`
   - `wokwi/diagram.json`

3. Install the Wokwi libraries listed in `wokwi/README.md`, then start the simulation.
4. Refresh the dashboard or select **Settings → Reload data**.

The receiver subscribes to `grainguard/demo/s01/ambient` on the HiveMQ public broker and appends valid readings to `mqtt_readings.csv`.

## Run verification checks

```powershell
python test_suite.py
```

The test suite checks synthetic-data structure, intended hotspot scenarios, MQTT schema, dashboard data resilience, USDA data preparation, model compatibility, prediction aggregation, and cost-calculator edge cases.

## Notes and limitations

- The supplied probe readings are synthetic, designed to demonstrate three review scenarios.
- The model prediction is an additional prioritisation signal; the dashboard's review state is based on the configurable temperature-rise rule.
- Any real deployment would require calibrated sensors, secure MQTT credentials, persistent storage, alerting, and domain-approved operating procedures.
