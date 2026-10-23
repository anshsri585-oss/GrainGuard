"""
GrainGuard dashboard (simplified, sidebar-navigation version).

Run from the project folder:   streamlit run dashboard.py

Data kinds are kept separate and labelled everywhere:
  * Synthetic  - the 16 simulated stacks (data/synthetic/)
  * Live       - Wokwi ESP32 + DHT22 ambient readings via MQTT (mqtt_readings.csv)
  * Real       - published USDA experiment (data/real/)
"""
from datetime import datetime
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
SENSOR_FILE = BASE_DIR / "data" / "synthetic" / "sensor_data.csv"
PRED_FILE = BASE_DIR / "data" / "synthetic" / "latest_predictions.csv"
MQTT_FILE = BASE_DIR / "mqtt_readings.csv"
ENV_FILE = BASE_DIR / "data" / "real" / "grainguard_usda_daily_environment.csv"
OUTCOME_FILE = BASE_DIR / "data" / "real" / "grainguard_usda_sample_outcomes.csv"

PAGES = ["Overview", "Stack monitoring", "Inspections", "Sensor status", "Reports & analysis"]
BASELINE_READINGS = 24      # baseline = mean of each probe's first 24 readings (less noisy than 1 reading)
PROBES_PER_STACK = 3
POSITION_LABEL = {"upper": "Upper", "middle": "Middle", "lower": "Lower"}

st.set_page_config(page_title="GrainGuard", page_icon="🌾", layout="wide")

# ----------------------------------------------------------------------------
# STYLE
# ----------------------------------------------------------------------------
st.markdown("""
<style>
section[data-testid="stSidebar"]{background:#0F3D2E;}
section[data-testid="stSidebar"] *{color:#E6F2EB;}
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child{display:none;}
section[data-testid="stSidebar"] div[role="radiogroup"] label{
  padding:10px 14px;border-radius:10px;width:100%;margin-bottom:2px;cursor:pointer;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){background:#1F5C41;font-weight:700;}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:#17503A;}
.gg-brand{font-size:22px;font-weight:700;display:flex;gap:10px;align-items:center;}
.gg-sub{font-size:13px;opacity:.8;margin:2px 0 14px 34px;}
.gg-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
.gg-title{font-size:34px;font-weight:700;line-height:1.1;}
.gg-subtitle{opacity:.75;margin-top:4px;}
.gg-badge{background:#9BE8BE;color:#0B3B28;font-weight:700;font-size:12px;padding:6px 12px;border-radius:8px;white-space:nowrap;}
.gg-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:14px 0 6px;}
.gg-metric{border:1px solid #3A443E;border-radius:12px;padding:16px 18px;background:#1F2522;}
.gg-metric .l{font-size:14px;opacity:.8;} .gg-metric .v{font-size:34px;font-weight:700;margin-top:2px;}
.gg-table{width:100%;border-collapse:collapse;border:1px solid #3A443E;border-radius:10px;overflow:hidden;font-size:14px;}
.gg-table th{background:#262D29;text-align:left;padding:10px 14px;font-size:12px;letter-spacing:.05em;opacity:.85;}
.gg-table td{padding:9px 14px;border-top:1px solid #333C37;}
.ok{color:#4ADE80;} .warn{color:#FBBF24;} .mute{color:#9CA3AF;}
.gg-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;}
.d-ok{background:#4ADE80;} .d-warn{background:#FBBF24;} .d-mute{background:#9CA3AF;} .d-bad{background:#F87171;}
.gg-chip{font-size:12px;font-weight:700;padding:4px 12px;border-radius:99px;background:#4A3410;color:#FBBF24;}
.gg-tag{display:inline-block;font-size:12px;padding:3px 10px;border-radius:6px;border:1px solid #3A443E;margin-right:6px;opacity:.9;}
.gg-icon{width:42px;height:42px;border-radius:10px;background:#FDE3C8;color:#9A3E00;display:flex;align-items:center;justify-content:center;font-weight:700;}
.gg-statusrow{display:flex;justify-content:space-between;padding:10px 2px;border-top:1px solid #333C37;font-size:15px;}
.gg-statusrow:first-of-type{border-top:none;}
.gg-h2{font-size:22px;font-weight:700;margin:22px 0 2px;}
@media (max-width:760px){.gg-metrics{grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# SMALL HELPERS
# ----------------------------------------------------------------------------
def page_header(title, subtitle):
    st.markdown(
        f'<div class="gg-head"><div><div class="gg-title">{escape(title)}</div>'
        f'<div class="gg-subtitle">{escape(subtitle)}</div></div>'
        f'<div class="gg-badge">DEMO DATA</div></div>', unsafe_allow_html=True)


def tags(*labels):
    st.markdown("".join(f'<span class="gg-tag">{escape(t)}</span>' for t in labels), unsafe_allow_html=True)


def h2(text):
    st.markdown(f'<div class="gg-h2">{escape(text)}</div>', unsafe_allow_html=True)


def status_row(label, state, text):
    dot = {"ok": "d-ok", "warn": "d-warn", "mute": "d-mute", "bad": "d-bad"}[state]
    cls = {"ok": "ok", "warn": "warn", "mute": "mute", "bad": "warn"}[state]
    return (f'<div class="gg-statusrow"><span>{escape(label)}</span>'
            f'<span class="{cls}"><span class="gg-dot {dot}"></span>{escape(text)}</span></div>')


def go_to(page, stack=None):
    """Button callback: jump to a page, optionally pre-selecting a stack."""
    if stack is not None:
        st.session_state["stack_choice"] = stack
    st.session_state["page"] = page


def stack_selector(options, key, label="Select stack"):
    """Selectbox whose choice is remembered when you move between pages."""
    current = st.session_state.get("stack_choice", options[0])
    if current not in options:
        current = options[0]

    def _remember():
        st.session_state["stack_choice"] = st.session_state[key]

    return st.selectbox(label, options, index=options.index(current), key=key, on_change=_remember)


@st.cache_data(show_spinner=False)
def read_csv_cached(path_str, mtime):
    """Re-reads only when the file changes (mtime is part of the cache key)."""
    return pd.read_csv(path_str)


def read_file(path):
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        return read_csv_cached(str(path), path.stat().st_mtime)
    except OSError as err:
        raise err


# ----------------------------------------------------------------------------
# DATA LOADING + THE ONE SHARED ALERT CALCULATION
# ----------------------------------------------------------------------------
def load_stack_data():
    """Returns (dataframe or None, problem message or None)."""
    if not SENSOR_FILE.is_file():
        return None, "Synthetic sensor file not found. Run `python simulator.py` first."
    try:
        df = read_file(SENSOR_FILE).copy()
    except (FileNotFoundError, OSError, Exception) as err:  # unreadable / corrupt file
        return None, f"Could not read sensor_data.csv: {err}"
    needed = {"timestamp", "stack_id", "probe_id", "position", "temperature_c"}
    if not needed.issubset(df.columns):
        return None, f"sensor_data.csv is missing columns: {', '.join(sorted(needed - set(df.columns)))}"
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601", errors="coerce")
    df["temperature_c"] = pd.to_numeric(df["temperature_c"], errors="coerce")
    df = df.dropna(subset=["timestamp", "temperature_c", "stack_id", "probe_id"])
    if df.empty:
        return None, "sensor_data.csv has no usable rows. Run `python simulator.py`."
    return df, None


def compute_status(df, threshold):
    """
    The single place where rises and review flags are calculated.
      baseline = mean of each probe's first BASELINE_READINGS readings
      latest   = each probe's most recent reading
      rise     = latest - baseline            (review if rise >= threshold)
    A stack is flagged if ANY of its probes is flagged.
    """
    df = df.sort_values(["stack_id", "probe_id", "timestamp"])
    keys = ["stack_id", "probe_id"]
    baseline = (df.groupby(keys).head(BASELINE_READINGS)
                .groupby(keys)["temperature_c"].mean().rename("baseline_c").reset_index())
    probes = df.groupby(keys).tail(1).merge(baseline, on=keys)
    probes["rise_c"] = probes["temperature_c"] - probes["baseline_c"]
    probes["needs_review"] = probes["rise_c"] >= threshold
    newest = df["timestamp"].max()
    probes["behind_latest"] = probes["timestamp"] < newest

    rows = []
    for stack, grp in probes.groupby("stack_id"):
        worst = grp.loc[grp["rise_c"].idxmax()]
        rows.append({
            "stack_id": stack,
            "max_temp": grp["temperature_c"].max(),
            "max_rise": worst["rise_c"],
            "worst_position": POSITION_LABEL.get(str(worst["position"]).lower(), str(worst["position"])),
            "review": bool(grp["needs_review"].any()),
            "probes": len(grp),
            "late_probes": int(grp["behind_latest"].sum()),
        })
    summary = pd.DataFrame(rows).sort_values("stack_id").reset_index(drop=True)
    return probes, summary, newest


def get_mqtt_status(stale_minutes):
    """Returns (state, message, dataframe or None). state: ok / warn / mute / bad."""
    if not MQTT_FILE.exists():
        return "mute", "Not started (run mqtt_receiver.py)", None
    try:
        m = pd.read_csv(MQTT_FILE)
    except Exception:
        return "bad", "File unreadable", None
    needed = {"timestamp", "temperature_c", "humidity_pct"}
    if not needed.issubset(m.columns):
        return "bad", "Unexpected columns in mqtt_readings.csv", None
    m["timestamp"] = pd.to_datetime(m["timestamp"], format="ISO8601", errors="coerce")
    m["temperature_c"] = pd.to_numeric(m["temperature_c"], errors="coerce")
    m["humidity_pct"] = pd.to_numeric(m["humidity_pct"], errors="coerce")
    m = m.dropna(subset=["timestamp", "temperature_c", "humidity_pct"]).sort_values("timestamp")
    if m.empty:
        return "mute", "No readings yet", None
    age_min = max((datetime.now() - m["timestamp"].iloc[-1]).total_seconds() / 60, 0)
    if age_min > stale_minutes:
        return "warn", f"Stale: last reading {age_min:,.0f} min ago", m
    return "ok", f"Receiving: last reading {age_min:,.0f} min ago", m


def load_predictions(summary):
    """Returns (dataframe or None, state, message). Checks the file matches the current sensor data."""
    if not PRED_FILE.exists():
        return None, "mute", "Not generated (run predict_hotspot.py)"
    try:
        p = read_file(PRED_FILE).copy()
    except Exception:
        return None, "bad", "File unreadable"
    needed = {"stack_id", "current_temp", "predicted_event_probability", "prediction_label"}
    if not needed.issubset(p.columns):
        return None, "bad", "Unexpected columns in latest_predictions.csv"
    merged = summary[["stack_id", "max_temp"]].merge(p[["stack_id", "current_temp"]], on="stack_id", how="outer")
    mismatch = (merged["max_temp"] - merged["current_temp"]).abs().fillna(99) > 0.011
    if mismatch.any():
        return p, "warn", "Out of date (re-run predict_hotspot.py)"
    return p, "ok", "Available and matches current sensor data"


# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state["page"] = "Overview"
if "inspection_log" not in st.session_state:
    st.session_state["inspection_log"] = []

with st.sidebar:
    st.markdown('<div class="gg-brand"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
                'stroke="#4ADE80" stroke-width="2" stroke-linecap="round"><path d="M12 21V11"/>'
                '<path d="M12 11C12 7 9 5 5 5c0 4 2 6 7 6z"/><path d="M12 13c0-4 3-6 7-6 0 4-2 6-7 6z"/></svg>'
                'GrainGuard</div><div class="gg-sub">Storage monitoring</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, key="page", label_visibility="collapsed")
    st.divider()
    with st.expander("Settings"):
        threshold = st.number_input(
            "Review threshold (°C rise)", min_value=0.5, max_value=10.0, value=2.0, step=0.5,
            help="Demonstration value only. It is not a scientifically validated spoilage threshold.")
        stale_minutes = st.number_input("Live sensor 'stale' after (minutes)", min_value=1, max_value=240, value=10, step=1)

# ----------------------------------------------------------------------------
# LOAD STACK DATA (every page needs it)
# ----------------------------------------------------------------------------
stack_df, problem = load_stack_data()
if problem:
    page_header(page, "Waiting for data")
    st.error(problem)
    st.stop()

probes, summary, newest = compute_status(stack_df, threshold)
stack_ids = list(summary["stack_id"])
n_stacks = len(summary)
n_review = int(summary["review"].sum())
late_total = int(summary["late_probes"].sum())


# ----------------------------------------------------------------------------
# PAGE: OVERVIEW
# ----------------------------------------------------------------------------
def page_overview():
    page_header("Overview", "Monitor your grain storage at a glance.")
    tags("Synthetic stack data")
    st.markdown(
        f'<div class="gg-metrics">'
        f'<div class="gg-metric"><div class="l">Stacks monitored</div><div class="v">{n_stacks}</div></div>'
        f'<div class="gg-metric"><div class="l">Need review</div><div class="v">{n_review}</div></div>'
        f'<div class="gg-metric"><div class="l">Probe streams</div><div class="v">{len(probes)}</div></div></div>',
        unsafe_allow_html=True)
    st.caption(f"Latest reading: {newest:%d %b %Y, %H:%M}")

    h2("Stacks needing attention")
    st.caption("Review temperature changes before deciding on any intervention.")
    flagged = summary[summary["review"]].sort_values("max_rise", ascending=False)
    if flagged.empty:
        st.success(f"No stack meets the demonstration review rule (rise ≥ {threshold:.1f} °C). "
                   "This does not guarantee the grain is healthy.")
    else:
        with st.container(border=True):
            for _, r in flagged.iterrows():
                c_icon, c_text, c_chip, c_btn = st.columns([0.7, 5, 1.6, 1.2])
                c_icon.markdown('<div class="gg-icon">T</div>', unsafe_allow_html=True)
                c_text.markdown(f"**Stack {escape(r['stack_id'])}**  \n"
                                f"{r['worst_position']} probe · {r['max_rise']:+.1f}°C rise")
                c_chip.markdown('<span class="gg-chip">Review</span>', unsafe_allow_html=True)
                c_btn.button("Open ›", key=f"open_{r['stack_id']}", on_click=go_to,
                             args=("Stack monitoring", r["stack_id"]))
    st.caption("ⓘ Illustrative demo readings. A temperature rise indicates a need for review, "
               "not confirmed spoilage.")

    h2("All stacks")
    rows = ""
    for _, r in summary.iterrows():
        status = ('<span class="warn"><span class="gg-dot d-warn"></span>Review</span>' if r["review"]
                  else '<span class="ok"><span class="gg-dot d-ok"></span>No review flag</span>')
        rows += (f"<tr><td><b>{escape(r['stack_id'])}</b></td><td>{status}</td>"
                 f"<td>{r['max_temp']:.1f} °C</td><td><b>{r['max_rise']:+.1f}°C</b></td></tr>")
    st.markdown(f'<table class="gg-table"><tr><th>STACK</th><th>STATUS</th><th>MAX TEMP</th>'
                f'<th>RISE</th></tr>{rows}</table>', unsafe_allow_html=True)
    st.caption(f"{n_stacks} total. Rise = latest reading minus the probe's starting baseline (largest of 3 probes).")
    c1, c2 = st.columns([3, 1])
    pick = c1.selectbox("View a stack in detail", stack_ids, key="overview_pick")
    c2.write("")
    c2.write("")
    c2.button("View details", on_click=go_to, args=("Stack monitoring", pick))

    h2("System status")
    mqtt_state, mqtt_msg, _ = get_mqtt_status(stale_minutes)
    _, pred_state, pred_msg = load_predictions(summary)
    cov_state = "ok" if late_total == 0 else "warn"
    cov_msg = (f"All {len(probes)} probes reporting" if late_total == 0
               else f"{late_total} probe(s) behind the latest reading")
    with st.container(border=True):
        st.markdown(
            status_row("Synthetic stack data", "ok", "Available") +
            status_row("Probe coverage", cov_state, cov_msg) +
            status_row("MQTT ambient sensor (Wokwi)", mqtt_state, mqtt_msg) +
            status_row("Experimental ML scores", pred_state, pred_msg), unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# PAGE: STACK MONITORING
# ----------------------------------------------------------------------------
def page_stack():
    page_header("Stack monitoring", "Temperature history and latest readings for one stack.")
    tags("Synthetic stack data")
    selected = stack_selector(stack_ids, key="sel_monitor")
    row = summary[summary["stack_id"] == selected].iloc[0]
    if row["review"]:
        st.warning(f"{selected}: at least one probe is {threshold:.1f} °C or more above its baseline. "
                   "Physical inspection recommended.")
    else:
        st.success(f"{selected}: no probe meets the review rule right now.")

    data = stack_df[stack_df["stack_id"] == selected]
    chart = data.pivot_table(index="timestamp", columns="position", values="temperature_c", aggfunc="mean")
    chart = chart[[c for c in ["upper", "middle", "lower"] if c in chart.columns]]
    chart.columns = [POSITION_LABEL.get(c, c) for c in chart.columns]
    h2("Temperature history")
    st.line_chart(chart)

    h2("Latest probe readings")
    table = probes[probes["stack_id"] == selected].copy()
    table["Position"] = table["position"].str.lower().map(POSITION_LABEL).fillna(table["position"])
    table["Status"] = table["needs_review"].map({True: "Review", False: "No review flag"})
    out = table[["probe_id", "Position", "temperature_c", "baseline_c", "rise_c", "Status"]].rename(columns={
        "probe_id": "Probe", "temperature_c": "Latest (°C)", "baseline_c": "Baseline (°C)", "rise_c": "Rise (°C)"})
    st.dataframe(out.round(2), hide_index=True)
    if row["late_probes"]:
        st.warning(f"{int(row['late_probes'])} probe(s) of this stack have no reading at the latest timestamp.")
    with st.expander("How the review flag works"):
        st.write(
            f"Each probe's baseline is the average of its first {BASELINE_READINGS} readings. "
            f"A probe is flagged when its latest reading is at least {threshold:.1f} °C above that baseline, "
            "and a stack is flagged if any of its three probes (upper, middle, lower) is flagged. "
            "The threshold is a demonstration setting, not a validated spoilage limit. "
            "A flag means: go and check the stack.")
    st.button("Go to inspection for this stack", on_click=go_to, args=("Inspections", selected))


# ----------------------------------------------------------------------------
# PAGE: INSPECTIONS (+ cost comparison)
# ----------------------------------------------------------------------------
FINDINGS = ["Not inspected", "No visible problem", "Excess moisture",
            "Suspected fungal growth", "Confirmed insect infestation"]


def page_inspections():
    page_header("Inspections", "Record what you find. Decisions stay with the operator.")
    st.caption("Human-in-the-loop decision support only. Temperature flags trigger a physical "
               "inspection, never automatic chemical application.")
    selected = stack_selector(stack_ids, key="sel_inspect", label="Select stack for physical inspection")
    row = summary[summary["stack_id"] == selected].iloc[0]
    if row["review"]:
        st.warning(f"{selected}: temperature rise of {row['max_rise']:+.1f} °C detected. "
                   "Physical inspection recommended.")
    else:
        st.info(f"{selected}: no current review flag. Continue scheduled routine monitoring.")

    finding = st.selectbox("What did the physical inspection find?", FINDINGS, key="finding")
    if finding == "Not inspected":
        st.info("Physical inspection is required before any intervention is considered.")
    elif finding == "No visible problem":
        st.success("Normal condition confirmed. Continue routine monitoring.")
    elif finding == "Excess moisture":
        st.warning("Investigate roof leaks and grain moisture content. Arrange aeration, drying or "
                   "ventilation according to approved grain-storage standards.")
    elif finding == "Suspected fungal growth":
        st.error("Isolate affected grain where appropriate and arrange a professional quality "
                 "assessment (mould, heating, mycotoxins).")
    else:
        st.warning("Insect infestation confirmed by physical inspection. Refer for authorised, "
                   "targeted pest management.")

    if finding != "Not inspected" and st.button("Save inspection record"):
        st.session_state["inspection_log"].append(
            {"Time": datetime.now().strftime("%H:%M:%S"), "Stack": selected, "Finding": finding})
        st.success("Inspection record saved for this session.")

    if finding == "Confirmed insect infestation":
        approved = st.checkbox("Authorised grain-storage operator approval recorded", key="approved")
        if approved and st.button("Simulate targeted treatment"):
            st.session_state["inspection_log"].append(
                {"Time": datetime.now().strftime("%H:%M:%S"), "Stack": selected,
                 "Finding": "Confirmed insect infestation (simulated treatment approved)"})
            st.success("Simulated treatment logged. No physical or chemical actuator was activated.")

    log = st.session_state["inspection_log"]
    if log:
        with st.expander(f"Session inspection log ({len(log)} records)"):
            st.dataframe(pd.DataFrame(log), hide_index=True)
            st.caption("Kept only while this browser session is open; it is not written to disk.")

    # ---- cost comparison -------------------------------------------------
    h2("Treatment cost comparison")
    st.caption("Illustrative comparison only, based on the assumptions you enter. "
               "Not verified savings from a real warehouse.")
    logged = {e["Stack"] for e in log if e["Finding"].startswith("Confirmed insect")}
    use_log = st.checkbox(f"Use confirmed stacks from this session's log ({len(logged)} recorded)", value=False)
    if use_log:
        confirmed = min(len(logged), n_stacks)
        st.write(f"Confirmed stacks used: **{confirmed}**")
    else:
        confirmed = st.number_input("Stacks with confirmed insect infestation (from physical inspection)",
                                    min_value=0, max_value=n_stacks, value=min(2, n_stacks), step=1)
    cost_per_stack = st.number_input("Estimated treatment cost per stack (₹ INR)",
                                     min_value=0.0, value=500.0, step=50.0)
    baseline = n_stacks * cost_per_stack
    targeted = confirmed * cost_per_stack
    avoided = baseline - targeted
    pct = (avoided / baseline * 100) if baseline > 0 else 0.0
    c1, c2, c3 = st.columns(3)
    c1.metric("Treat-all baseline", f"₹{baseline:,.2f}")
    c2.metric("Targeted treatment", f"₹{targeted:,.2f}")
    c3.metric("Illustrative avoided cost", f"₹{avoided:,.2f}")
    st.caption(f"Hypothetical cost difference: {pct:.1f}% of the treat-all baseline.")
    if confirmed == 0:
        st.warning("With 0 confirmed stacks the targeted cost is ₹0. That assumes no treatment is needed, "
                   "so treat this figure as hypothetical.")
    st.bar_chart(pd.DataFrame({"Estimated cost (₹)": [baseline, targeted]},
                              index=["Treat all stacks", "Treat confirmed stacks"]))
    st.info("**Assumptions and limits**\n\n"
            f"- Treat-all = {n_stacks} stacks × cost per stack; targeted = confirmed stacks × cost per stack.\n"
            "- Excludes inspection labour, protective equipment, monitoring sensors, downtime and "
            "treatment-specific requirements.\n"
            "- Treatments must follow local agricultural rules and safety protocols.")


# ----------------------------------------------------------------------------
# PAGE: SENSOR STATUS (live Wokwi / MQTT)
# ----------------------------------------------------------------------------
def page_sensor():
    page_header("Sensor status", "Live ambient readings from the Wokwi ESP32 + DHT22 simulation.")
    tags("Live: Wokwi simulation")
    state, msg, m = get_mqtt_status(stale_minutes)
    with st.container(border=True):
        st.markdown(status_row("MQTT ambient sensor", state, msg), unsafe_allow_html=True)
    st.button("Refresh now")
    if m is None:
        st.info("Pipeline: Wokwi ESP32 + DHT22 → Wi-Fi → HiveMQ broker → `mqtt_receiver.py` → "
                "`mqtt_readings.csv` → this page. Start the receiver and the Wokwi simulation to see data.")
    else:
        last = m.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Monitored stack", str(last.get("stack_id", "n/a")))
        c2.metric("Ambient temperature", f"{last['temperature_c']:.1f} °C")
        c3.metric("Relative humidity", f"{last['humidity_pct']:.1f} %")
        st.caption(f"Last received: {last['timestamp']:%d %b %Y, %H:%M:%S}. "
                   "Timestamps are when the receiver got the message.")
        if not (-10 <= last["temperature_c"] <= 60) or not (0 <= last["humidity_pct"] <= 100):
            st.warning("The latest reading is outside a plausible range. Check the sensor values.")
        h2("Ambient temperature history")
        st.line_chart(m.set_index("timestamp")["temperature_c"])
        h2("Relative humidity history")
        st.line_chart(m.set_index("timestamp")["humidity_pct"])
    st.info("The DHT22 measures ambient air temperature and humidity only. It does not measure grain "
            "moisture or detect insects, and it is not one of the 48 simulated stack probes.")


# ----------------------------------------------------------------------------
# PAGE: REPORTS & ANALYSIS
# ----------------------------------------------------------------------------
def tab_usda():
    tags("Real: USDA experiment")
    st.caption("Published laboratory experiment. These are not measurements of the 16 simulated stacks.")
    if not ENV_FILE.exists() or not OUTCOME_FILE.exists():
        st.error("USDA files not found. Both CSV files must be inside data/real/.")
        return
    try:
        env = read_file(ENV_FILE).copy()
        out = read_file(OUTCOME_FILE).copy()
        env["date"] = pd.to_datetime(env["date"], errors="coerce")
        n_before = len(env)
        env = env.drop_duplicates().dropna(subset=["date"])
        dupes = n_before - len(env)
        treatments = sorted(env["treatment"].dropna().unique())
        sel = st.selectbox("Experimental treatment", treatments)
        daily = (env[env["treatment"] == sel].groupby("date")
                 .agg(temperature=("temperature_c", "mean"), humidity=("relative_humidity_pct", "mean")).sort_index())
        c1, c2 = st.columns(2)
        c1.subheader("Temperature history")
        c1.line_chart(daily["temperature"])
        c2.subheader("Relative humidity history")
        c2.line_chart(daily["humidity"])
        notes = "Each point is the average of the replicates for that date."
        if dupes:
            notes += f" {dupes} exact duplicate row(s) were ignored."
        if "temperature_measurements" in env.columns:
            usual = env["temperature_measurements"].mode().iloc[0]
            odd = int((env["temperature_measurements"] != usual).sum())
            if odd:
                notes += (f" {odd} row(s) summarise a different number of readings than the usual {int(usual)} "
                          "per day and are shown as given.")
        st.caption(notes)

        st.subheader("Grain and insect outcomes by treatment")
        agg = out.groupby("treatment").agg(
            samples=("replicate", "count"),
            with_progeny=("insect_progeny_detected", "sum"),
            grain_moisture_pct=("grain_moisture_pct", "mean"),
            insect_progeny=("insect_progeny", "mean"),
            adult_insects=("adult_insects", "mean"),
            frass_weight_g=("frass_weight_g", "mean")).round(2)
        agg = agg.rename(columns={"with_progeny": "samples with progeny"})
        st.dataframe(agg)
        c1, c2 = st.columns(2)
        c1.subheader("Mean insect progeny")
        c1.bar_chart(agg["insect_progeny"])
        c2.subheader("Mean grain moisture (%)")
        c2.bar_chart(agg["grain_moisture_pct"])
        st.info("Each treatment has only a handful of samples, so these are descriptive summaries, not "
                "statistical conclusions. Insect counts reflect the experimental set-up; insect progeny is "
                "not a direct spoilage label. Treatment codes follow the source dataset; check the USDA "
                "publication for their full definitions.")
    except KeyError as err:
        st.error(f"Missing required research-data column: {err}")


def tab_ml():
    tags("Synthetic only")
    st.warning("Experimental. This model was trained and tested on artificial temperature scenarios only. "
               "Its score is not a calibrated probability and says nothing proven about real grain spoilage.")
    pred, state, msg = load_predictions(summary)
    if pred is None:
        st.info(f"Prediction file status: {msg}")
        return
    if state == "warn":
        st.warning(f"The prediction file does not match the current sensor data ({msg}). "
                   "Scores below may be outdated.")
    show = summary[["stack_id", "review"]].merge(pred, on="stack_id", how="left")
    show["Experimental score"] = show.apply(
        lambda r: "Not applicable (already flagged)" if r["review"]
        else ("n/a" if pd.isna(r["predicted_event_probability"]) else f"{r['predicted_event_probability'] * 100:.0f}"),
        axis=1)
    show["Model output"] = show.apply(
        lambda r: "-" if r["review"] or pd.isna(r["prediction_label"]) else r["prediction_label"], axis=1)
    show["Current status"] = show["review"].map({True: "Review", False: "No review flag"})
    st.dataframe(show[["stack_id", "Current status", "Experimental score", "Model output"]]
                 .rename(columns={"stack_id": "Stack"}), hide_index=True)
    st.caption("The score estimates whether a synthetic heating event is about to start. It is meaningless once "
               "heating is already under way, so flagged stacks are excluded. In testing this prototype also "
               "raised false alarms on stacks with no heating, so use the temperature review flag first.")


def page_reports():
    page_header("Reports & analysis", "Research data and experimental models, kept separate from live monitoring.")
    t1, t2 = st.tabs(["USDA research data (real)", "Experimental ML (synthetic only)"])
    with t1:
        tab_usda()
    with t2:
        tab_ml()


# ----------------------------------------------------------------------------
# ROUTER
# ----------------------------------------------------------------------------
{"Overview": page_overview, "Stack monitoring": page_stack, "Inspections": page_inspections,
 "Sensor status": page_sensor, "Reports & analysis": page_reports}[page]()
