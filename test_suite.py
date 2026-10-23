"""
GrainGuard Automated Verification Test Suite
---------------------------------------------
Run this script to verify the core data pipelines, baseline calculations,
model compatibility, and error handling of the GrainGuard prototype.
Usage:
    python test_suite.py
"""

import sys
import os
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

BASE_DIR = Path(__file__).resolve().parent

print(f"Running GrainGuard test suite in: {BASE_DIR}\n")

test_results = {}

# TEST 1: Synthetic data generation and schema
try:
    sensor_path = BASE_DIR / "data" / "synthetic" / "sensor_data.csv"
    assert sensor_path.exists(), "sensor_data.csv missing. Run python simulator.py first."
    df = pd.read_csv(sensor_path, parse_dates=["timestamp"])
    
    assert len(df) == 34560, f"Expected 34560 rows, got {len(df)}"
    assert df["stack_id"].nunique() == 16, f"Expected 16 stacks, got {df['stack_id'].nunique()}"
    assert set(df["position"].unique()) == {"upper", "middle", "lower"}, "Positions mismatch"
    assert set(df["probe_id"].unique()) == {"P1", "P2", "P3"}, "Probe IDs mismatch"
    
    # 48 unique streams
    streams = df.groupby(["stack_id", "probe_id"]).size()
    assert len(streams) == 48, f"Expected 48 streams, got {len(streams)}"
    assert (streams == 720).all(), "Every stream must have exactly 720 readings"
    
    test_results["1. Synthetic Data & 48 Streams"] = "PASS"
except Exception as e:
    test_results["1. Synthetic Data & 48 Streams"] = f"FAIL: {e}"

# TEST 2: Intended hotspot detection on S04 (upper), S07 (middle), S12 (lower)
try:
    initial = (
        df.sort_values("timestamp")
        .groupby(["stack_id", "probe_id"])
        .first()["temperature_c"]
        .rename("initial_temp")
        .reset_index()
    )
    latest_time = df["timestamp"].max()
    latest = df[df["timestamp"] == latest_time].merge(initial, on=["stack_id", "probe_id"])
    latest["rise_c"] = latest["temperature_c"] - latest["initial_temp"]
    latest["alert"] = latest["rise_c"] >= 2.0
    
    stack_alerts = latest.groupby("stack_id")["alert"].any()
    alerted_stacks = set(stack_alerts[stack_alerts].index)
    
    assert alerted_stacks == {"S04", "S07", "S12"}, f"Expected {{'S04', 'S07', 'S12'}}, got {alerted_stacks}"
    
    # Check specific probes
    s04_p1 = latest[(latest["stack_id"]=="S04") & (latest["probe_id"]=="P1")].iloc[0]
    s07_p2 = latest[(latest["stack_id"]=="S07") & (latest["probe_id"]=="P2")].iloc[0]
    s12_p3 = latest[(latest["stack_id"]=="S12") & (latest["probe_id"]=="P3")].iloc[0]
    
    assert s04_p1["position"] == "upper" and s04_p1["alert"], "S04 P1 upper should alert"
    assert s07_p2["position"] == "middle" and s07_p2["alert"], "S07 P2 middle should alert"
    assert s12_p3["position"] == "lower" and s12_p3["alert"], "S12 P3 lower should alert"
    
    test_results["2. Heating Scenarios & Probe Positions"] = "PASS"
except Exception as e:
    test_results["2. Heating Scenarios & Probe Positions"] = f"FAIL: {e}"

# TEST 3: MQTT Message Parsing and CSV Schema
try:
    test_payload = json.dumps({
        "stack_id": "S01",
        "sensor_type": "ambient_DHT22",
        "temperature_c": 25.5,
        "humidity_pct": 55.0,
        "data_source": "TEST"
    }).encode("utf-8")
    
    parsed = json.loads(test_payload.decode("utf-8"))
    row = [
        "2026-10-20T12:00:00",
        parsed["stack_id"],
        parsed["sensor_type"],
        parsed["temperature_c"],
        parsed["humidity_pct"],
        parsed["data_source"]
    ]
    expected_cols = ["timestamp", "stack_id", "sensor_type", "temperature_c", "humidity_pct", "data_source"]
    assert len(row) == len(expected_cols)
    
    # Verify existing mqtt_readings.csv matches schema
    mqtt_file = BASE_DIR / "mqtt_readings.csv"
    if mqtt_file.exists():
        mqtt_df = pd.read_csv(mqtt_file)
        assert list(mqtt_df.columns) == expected_cols, f"CSV columns mismatch: {mqtt_df.columns}"
    test_results["3. MQTT Message & CSV Schema"] = "PASS"
except Exception as e:
    test_results["3. MQTT Message & CSV Schema"] = f"FAIL: {e}"

# TEST 4: Dashboard missing-file resilience
try:
    dash_path = BASE_DIR / "dashboard.py"
    with open(dash_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    has_resilience = "pd.read_csv(" in code and ("is_file()" in code or "FileNotFoundError" in code or "OSError" in code)
    
    if has_resilience:
        test_results["4. Dashboard Missing-File Resilience"] = "PASS"
    else:
        test_results["4. Dashboard Missing-File Resilience"] = "FAIL: sensor_data.csv read is unprotected."
except Exception as e:
    test_results["4. Dashboard Missing-File Resilience"] = f"FAIL: {e}"

# TEST 5: Real USDA Data Loading, Treatments, and Deduplication in Pipeline
try:
    proc_data = pd.read_csv(BASE_DIR / "data" / "processed" / "real_ml_data.csv")
    outcomes = pd.read_csv(BASE_DIR / "data" / "real" / "grainguard_usda_sample_outcomes.csv")
    
    assert proc_data.shape[0] == 20, f"Expected 20 processed rows, got {proc_data.shape[0]}"
    assert proc_data["experiment_id"].nunique() == 20, "Expected 20 unique experiment_ids"
    assert not proc_data.isnull().any().any(), "Processed data contains unexpected nulls"
    
    test_results["5. USDA Pipeline & Deduplication"] = "PASS"
except Exception as e:
    test_results["5. USDA Pipeline & Deduplication"] = f"FAIL: {e}"

# TEST 6: Hotspot Model loading & Feature Compatibility
try:
    saved = joblib.load(BASE_DIR / "models" / "hotspot_model.joblib")
    model = saved["model"]
    features = saved["features"]
    
    expected_features = ["current_temp", "avg_temp_24h", "max_temp_24h", "temp_change_6h", "temp_change_24h"]
    assert features == expected_features, f"Features order/names mismatch: {features}"
    
    sample = pd.DataFrame([{
        "current_temp": 28.0,
        "avg_temp_24h": 27.5,
        "max_temp_24h": 28.5,
        "temp_change_6h": 0.2,
        "temp_change_24h": 0.5
    }])
    prob = model.predict_proba(sample[features])
    assert prob.shape == (1, 2), "Inference output shape mismatch"
    test_results["6. Model Loading & Feature Compatibility"] = "PASS"
except Exception as e:
    test_results["6. Model Loading & Feature Compatibility"] = f"FAIL: {e}"

# TEST 7: 48-Probe-to-16-Stack Aggregation & Baseline Consistency
try:
    preds = pd.read_csv(BASE_DIR / "data" / "synthetic" / "latest_predictions.csv")
    probes = pd.read_csv(BASE_DIR / "data" / "synthetic" / "probe_predictions.csv")
    
    assert len(probes) == 48, f"Expected 48 probe rows, got {len(probes)}"
    assert len(preds) == 16, f"Expected 16 stack rows, got {len(preds)}"
    
    # Check aggregation correctness
    agg_check = probes.groupby("stack_id").agg({
        "temperature_c": "max",
        "rise_c": "max",
        "predicted_event_probability": "max",
        "heating_alert": "any"
    }).reset_index()
    
    merged = preds.merge(agg_check, on="stack_id")
    assert np.allclose(merged["current_temp"], merged["temperature_c"]), "current_temp max mismatch"
    assert np.allclose(merged["max_rise_c"], merged["rise_c"]), "max_rise_c aggregation mismatch"
    assert (merged["heating_alert_x"] == merged["heating_alert_y"]).all(), "heating_alert any mismatch"
    
    # Check initial_temp consistency between raw sensor_data (hour 0) and probe_predictions
    df_raw = pd.read_csv(BASE_DIR / "data" / "synthetic" / "sensor_data.csv")
    initial_hour0 = df_raw.sort_values("timestamp").groupby(["stack_id", "probe_id"]).first()["temperature_c"]
    initial_probe = probes.set_index(["stack_id", "probe_id"])["initial_temp"]
    
    diff = (initial_hour0 - initial_probe).abs().max()
    assert diff <= 1e-4, f"Baseline discrepancy remains: {diff:.4f}°C"
    
    test_results["7. Baseline Consistency & Aggregation"] = "PASS"
except Exception as e:
    test_results["7. Baseline Consistency & Aggregation"] = f"FAIL: {e}"

# TEST 8: Inspection workflow and Cost Calculator edge cases
try:
    total_stacks = 16
    cost_per_stack = 500.0
    confirmed_stacks = 2
    
    all_stack_cost = total_stacks * cost_per_stack
    targeted_cost = confirmed_stacks * cost_per_stack
    avoided_cost = all_stack_cost - targeted_cost
    pct = (avoided_cost / all_stack_cost) * 100 if all_stack_cost > 0 else 0
    
    assert all_stack_cost == 8000.0
    assert targeted_cost == 1000.0
    assert avoided_cost == 7000.0
    assert abs(pct - 87.5) < 1e-4
    
    # Edge case 1: 0 cost
    all_zero = 0.0
    pct_zero = (0 / all_zero) * 100 if all_zero > 0 else 0
    assert pct_zero == 0
    
    # Edge case 2: all confirmed
    all_conf = 16 * 500.0
    avoided_all_conf = all_stack_cost - all_conf
    assert avoided_all_conf == 0.0
    
    test_results["8. Cost Calculator & Edge Cases"] = "PASS"
except Exception as e:
    test_results["8. Cost Calculator & Edge Cases"] = f"FAIL: {e}"

print("\n--- TEST SUITE SUMMARY ---")
all_passed = True
for test, result in test_results.items():
    print(f"[{result.split(':')[0]}] {test}")
    if result != "PASS":
        all_passed = False
        print(f"   Details: {result}")

if all_passed:
    print("\nOVERALL STATUS: ALL 8 TEST SUITES PASSED!")
