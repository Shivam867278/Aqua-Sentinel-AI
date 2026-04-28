import time
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from api_client import API_BASE_URL, api_get, api_patch, api_post
from config import settings
from local_ai import demand_fallback, leakage_fallback, optimize_fallback, quality_fallback
from simulator import REFRESH_SECONDS, asset_health, initialize_state, simulate_sensor_tick, zone_snapshot
from styles import inject_css
from ui_components import gauge, glass_end, glass_start, hero, kpi_card, section, status


DEVELOPER_NAME = settings.developer_name


st.set_page_config(
    page_title="Aqua Sentinel AI",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)


def line_chart(df: pd.DataFrame, columns: list[str], title: str) -> go.Figure:
    chart_df = df[["time", *columns]].melt("time", var_name="Sensor", value_name="Value")
    fig = px.line(chart_df, x="time", y="Value", color="Sensor", title=title, markers=False)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#dff6ff",
        title_font_size=18,
        margin=dict(l=12, r=12, t=52, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_traces(line=dict(width=3))
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)")
    return fig


def donut(value: float, title: str, color: str) -> go.Figure:
    value = max(0, min(100, value))
    fig = go.Figure(
        data=[
            go.Pie(
                values=[value, 100 - value],
                hole=0.72,
                marker_colors=[color, "rgba(255,255,255,0.08)"],
                textinfo="none",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=230,
        margin=dict(l=0, r=0, t=34, b=0),
        title=title,
        title_font_size=16,
        annotations=[
            dict(
                text=f"{value:.0f}%",
                x=0.5,
                y=0.5,
                font=dict(size=30, color="#ffffff"),
                showarrow=False,
            )
        ],
        showlegend=False,
    )
    return fig


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("## 💧 Aqua Sentinel")
        st.caption("Industrial AI water operations")
        user = st.session_state.get("current_user", {})
        if user:
            st.success(user.get("full_name", "User"))
            st.caption(f"{user.get('role', 'user').title()} - {user.get('city_name', 'City')}")
            if st.button("Logout"):
                st.session_state.pop("auth_token", None)
                st.session_state.pop("current_user", None)
                st.rerun()
        st.divider()
        selected = st.radio(
            "Navigate",
            [
                "Command Center",
                "My Water Account",
                "Leakage Detection",
                "Water Quality",
                "Demand Prediction",
                "Assets & Alerts",
                "Automatic Alarms",
                "Citizen Complaints",
                "Service Rating",
                "Water System Control",
                "AI Control Room",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        health = api_get("/health")
        if health:
            st.success("API online")
        else:
            st.warning("API offline")
        st.caption(f"Telemetry refresh: {REFRESH_SECONDS}s")
    return selected


def render_auth_screen() -> None:
    hero()
    section("Secure Smart City Access", "Login to monitor your city water network and save AI results.")
    login_col, register_col = st.columns((1, 1))

    with login_col:
        glass_start()
        st.subheader("City Login")
        email = st.text_input("Email", value="admin@aqua.local", key="login_email")
        password = st.text_input("Password", value="admin123", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            result = api_post("/auth/login", {"email": email, "password": password})
            if result and result.get("token"):
                st.session_state.auth_token = result["token"]
                st.session_state.current_user = result["user"]
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Login failed. Check your credentials.")
        st.caption("Demo: admin@aqua.local / admin123")
        st.caption("Also available: operator@aqua.local / operator123, citizen@aqua.local / citizen123")
        glass_end()

    with register_col:
        glass_start()
        st.subheader("Citizen Registration")
        full_name = st.text_input("Full Name", key="register_name")
        register_email = st.text_input("Email Address", key="register_email")
        register_password = st.text_input("Create Password", type="password", key="register_password")
        city_name = st.text_input("City Name", value="Smart Water City", key="register_city")
        if st.button("Create Account", key="register_button"):
            result = api_post(
                "/auth/register",
                {
                    "full_name": full_name,
                    "email": register_email,
                    "password": register_password,
                    "city_name": city_name,
                },
            )
            if result and result.get("token"):
                st.session_state.auth_token = result["token"]
                st.session_state.current_user = result["user"]
                st.success("Account created.")
                st.rerun()
            else:
                st.error("Could not create account. Use a unique email and 6+ character password.")
        glass_end()


def post_with_fallback(endpoint: str, payload: dict, fallback):
    result = api_post(endpoint, payload)
    if result:
        return result
    if settings.enable_local_fallback:
        st.info("Local AI mode active. Results are generated from the built-in simulation engine.")
        return fallback(payload)
    return None


def command_center() -> None:
    section("📊 Command Center", "Live view of hydraulic performance, demand, energy, and water loss.")
    latest = simulate_sensor_tick()
    scan_result = api_post(
        "/monitoring/scan",
        {
            "zone": "Central Grid",
            "flow_rate": latest["flow_rate"],
            "pressure": latest["pressure"],
            "demand": latest["demand"],
            "turbidity": latest["turbidity"],
            "loss": latest["loss"],
            "ph": 7.2,
            "chlorine": 0.6,
            "vibration": 0.25,
            "acoustic_noise": 34.0,
        },
    )
    if scan_result and scan_result.get("alarm_count", 0) > 0:
        st.session_state.latest_alarm = scan_result
    elif "latest_alarm" not in st.session_state:
        st.session_state.latest_alarm = None

    latest_alarm = st.session_state.get("latest_alarm")
    if latest_alarm and latest_alarm.get("alarm_count", 0) > 0:
        alarm_text = latest_alarm.get("alarms", [{}])[0].get("event", "Harmful scenario detected")
        status(f"Automatic Alarm: {alarm_text}. Operator attention required.", "danger")
    else:
        status("Automatic monitoring active. No harmful scenario detected.", "safe")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Flow Rate", f"{latest['flow_rate']:,.1f}", "L/min", "▲ Stable inflow", "🌊")
    with c2:
        trend = "⚠ Elevated" if latest["pressure"] > 5.5 else "▲ Optimal pressure"
        kpi_card("Pressure", f"{latest['pressure']:,.2f}", "bar", trend, "⚙️")
    with c3:
        kpi_card("Demand", f"{latest['demand']:,.0f}", "L/day", "▲ Forecast model active", "🏙️")
    with c4:
        kpi_card("Water Loss", f"{latest['loss']:,.1f}", "%", "▼ NRW optimizer tracking", "🧭")

    df = st.session_state.sensor_history.copy()

    left, right = st.columns((1.45, 1))
    with left:
        glass_start()
        st.plotly_chart(
            line_chart(df, ["flow_rate", "pressure", "demand"], "Live Sensor Telemetry"),
            use_container_width=True,
        )
        glass_end()

    with right:
        glass_start()
        st.plotly_chart(donut(100 - latest["loss"], "Network Efficiency", "#35d6ff"), use_container_width=True)
        gauge("Reservoir storage", 74.0)
        gauge("Pump efficiency", max(0, 100 - latest["energy"] * 0.42))
        gauge("Water quality confidence", max(0, 100 - latest["turbidity"] * 8))
        if latest["turbidity"] < 5 and latest["pressure"] < 5.5:
            status("✅ Operations normal. No immediate threat detected.", "safe")
        else:
            status("🚨 Attention required. One or more signals are outside target range.", "danger")
        glass_end()

    section("🗺️ Zone Intelligence", "Operational snapshot across monitored network areas.")
    zones = zone_snapshot()
    st.dataframe(
        zones,
        use_container_width=True,
        hide_index=True,
        column_config={
            "flow_rate": st.column_config.ProgressColumn("Flow L/min", min_value=0, max_value=140),
            "pressure": st.column_config.NumberColumn("Pressure bar", format="%.2f"),
            "loss_percent": st.column_config.ProgressColumn("Loss %", min_value=0, max_value=30),
        },
    )


def my_water_account() -> None:
    section("My Water Account", "Citizen water bill, tank level, motor status, quality report, and flow meter.")
    account = api_get("/citizen/water-account")
    if not account:
        status("Water account data is not available right now.", "warning")
        return

    profile = account.get("profile", {})
    bill = account.get("bill", {})
    tank = account.get("tank", {})
    motor = account.get("motor", {})
    quality = account.get("quality", {})
    flow_meter = account.get("flow_meter", {})

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Bill Amount", f"₹{bill.get('amount_due', 0):,.0f}", bill.get("status", "N/A"), "Due " + str(bill.get("due_date", "N/A")), "💳")
    with c2:
        kpi_card("Tank Level", f"{tank.get('level_percent', 0):.0f}", "%", f"{tank.get('estimated_available_liters', 0)} L available", "🛢️")
    with c3:
        kpi_card("Motor", motor.get("status", "N/A"), motor.get("mode", "N/A"), f"Health: {motor.get('health', 'N/A')}", "⚙️")
    with c4:
        kpi_card("Flow Meter", f"{flow_meter.get('current_flow_l_min', 0):.1f}", "L/min", f"Meter {flow_meter.get('meter_id', 'N/A')}", "📟")

    left, right = st.columns((1, 1))
    with left:
        glass_start()
        st.subheader("Connection Details")
        st.metric("Connection ID", profile.get("connection_id", "N/A"))
        st.write(profile.get("address", "Address not available"))
        gauge("Tank level", float(tank.get("level_percent", 0)))
        st.metric("Tank Capacity", f"{tank.get('capacity_liters', 0):,.0f} L")
        glass_end()

        glass_start()
        st.subheader("Water Bill")
        st.metric("Billing Month", bill.get("billing_month", "N/A"))
        st.metric("Consumption", f"{bill.get('consumption_kl', 0):.2f} kL")
        st.metric("Amount Due", f"₹{bill.get('amount_due', 0):,.0f}")
        status(f"Bill status: {bill.get('status', 'N/A')}", "safe" if bill.get("status") == "Paid" else "warning")
        glass_end()

    with right:
        glass_start()
        st.subheader("Quality Report")
        quality_state = "safe" if quality.get("status") == "Safe" else "danger"
        status(f"Water quality: {quality.get('status', 'N/A')}", quality_state)
        q1, q2, q3 = st.columns(3)
        with q1:
            st.metric("pH", quality.get("ph", "N/A"))
        with q2:
            st.metric("Turbidity", f"{quality.get('turbidity_ntu', 0)} NTU")
        with q3:
            st.metric("Chlorine", f"{quality.get('chlorine_mg_l', 0)} mg/L")
        st.metric("TDS", f"{quality.get('tds_ppm', 0)} ppm")
        st.caption(f"Last tested: {quality.get('last_tested', 'N/A')}")
        glass_end()

        glass_start()
        st.subheader("Motor & Flow Meter")
        st.metric("Motor Status", motor.get("status", "N/A"), motor.get("mode", "N/A"))
        st.metric("Last Motor Run", motor.get("last_run", "N/A"))
        st.metric("Pressure", f"{flow_meter.get('pressure_bar', 0):.2f} bar")
        st.metric("Today Usage", f"{flow_meter.get('today_usage_liters', 0):,.0f} L")
        st.metric("Monthly Usage", f"{flow_meter.get('month_usage_kl', 0):.2f} kL")
        glass_end()


def leakage_detection() -> None:
    section("🚨 Leakage Detection", "AI-assisted leak risk scoring using flow, pressure, vibration, and acoustic data.")
    col1, col2 = st.columns((1, 1))

    with col1:
        glass_start()
        st.subheader("Hydraulic Inputs")
        flow_rate = st.number_input("Flow Rate (L/min)", min_value=0.0, value=82.5, step=0.5)
        pressure = st.number_input("Pressure (bar)", min_value=0.0, value=4.1, step=0.1)
        vibration = st.number_input("Pipe Vibration Index", min_value=0.0, value=0.28, step=0.01)
        acoustic = st.number_input("Acoustic Noise (dB)", min_value=0.0, value=34.0, step=0.5)
        zone = st.selectbox("Network Zone", ["North Grid", "Central Grid", "Industrial East", "Residential West"])
        if st.button("Analyze Leakage Risk", key="leakage_button"):
            payload = {
                "flow_rate": flow_rate,
                "pressure": pressure,
                "vibration": vibration,
                "acoustic_noise": acoustic,
                "zone": zone,
            }
            with st.spinner("Running leakage detection model..."):
                time.sleep(0.9)
                result = post_with_fallback("/leakage", payload, leakage_fallback)
            if result:
                st.session_state.leakage_result = result
        glass_end()

    with col2:
        glass_start()
        st.subheader("Detection Feedback")
        result = st.session_state.get("leakage_result")
        if result:
            leak_detected = bool(result.get("leak_detected") or result.get("leakage"))
            confidence = result.get("confidence", "N/A")
            risk_score = float(result.get("risk_score", 0)) * 100
            if leak_detected:
                status(f"🚨 Danger: leakage signature detected. Confidence: {confidence}", "danger")
            else:
                status(f"✅ Safe: no leak signature detected. Confidence: {confidence}", "safe")
            gauge("Leak risk score", risk_score)
            st.info(result.get("recommendation", result.get("action", "Result generated successfully.")))
        else:
            status("🟢 Ready for analysis. Submit hydraulic readings to scan for leakage risk.", "safe")
        glass_end()


def water_quality() -> None:
    section("🧪 Water Quality", "Evaluate water safety from physical, chemical, and conductivity readings.")
    col1, col2, col3 = st.columns(3)
    with col1:
        ph = st.slider("pH Level", 0.0, 14.0, 7.2, 0.1)
        turbidity = st.slider("Turbidity (NTU)", 0.0, 20.0, 2.1, 0.1)
    with col2:
        tds = st.number_input("TDS (ppm)", min_value=0.0, value=320.0, step=5.0)
        temperature = st.number_input("Temperature (°C)", min_value=0.0, value=24.5, step=0.5)
    with col3:
        chlorine = st.number_input("Residual Chlorine (mg/L)", min_value=0.0, value=0.6, step=0.1)
        conductivity = st.number_input("Conductivity (µS/cm)", min_value=0.0, value=510.0, step=10.0)

    if st.button("Evaluate Water Quality", key="quality_button"):
        payload = {
            "ph": ph,
            "turbidity": turbidity,
            "tds": tds,
            "temperature": temperature,
            "chlorine": chlorine,
            "conductivity": conductivity,
        }
        with st.spinner("Processing water quality intelligence..."):
            time.sleep(0.9)
            result = post_with_fallback("/quality", payload, quality_fallback)
        if result:
            st.session_state.quality_result = result

    left, right = st.columns((1, 1))
    with left:
        glass_start()
        result = st.session_state.get("quality_result")
        if result:
            unsafe = bool(result.get("unsafe"))
            score = float(result.get("quality_score", 0))
            if unsafe:
                status("🚨 Danger: quality parameters require immediate attention.", "danger")
            else:
                status("✅ Safe: quality parameters are inside acceptable operating limits.", "safe")
            st.plotly_chart(donut(score, "Quality Score", "#19d3a2" if score > 70 else "#ff4b66"), use_container_width=True)
            st.info(result.get("recommendation", result.get("action", "Result generated successfully.")))
        else:
            status("🟢 Quality module ready. Enter values and run evaluation.", "safe")
        glass_end()
    with right:
        df = st.session_state.sensor_history.copy()
        glass_start()
        st.plotly_chart(line_chart(df, ["turbidity"], "Live Turbidity Trend"), use_container_width=True)
        glass_end()


def demand_prediction() -> None:
    section("📈 Demand Prediction", "Forecast near-term demand from population, weather, industry, and storage context.")
    left, right = st.columns((1, 1))
    with left:
        population = st.number_input("Service Population", min_value=1, value=12500, step=100)
        avg_temperature = st.number_input("Average Temperature (°C)", min_value=-10.0, value=29.0, step=0.5)
        rainfall = st.number_input("Rainfall (mm)", min_value=0.0, value=3.0, step=0.5)
    with right:
        day_type = st.selectbox("Day Type", ["Weekday", "Weekend", "Holiday"])
        industrial_load = st.slider("Industrial Load (%)", 0, 100, 62)
        current_storage = st.slider("Reservoir Storage (%)", 0, 100, 74)

    if st.button("Predict Demand", key="demand_button"):
        payload = {
            "population": population,
            "avg_temperature": avg_temperature,
            "rainfall": rainfall,
            "day_type": day_type,
            "industrial_load": industrial_load,
            "current_storage": current_storage,
        }
        with st.spinner("Forecasting water demand..."):
            time.sleep(0.9)
            result = post_with_fallback("/predict-demand", payload, demand_fallback)
        if result:
            st.session_state.demand_result = result

    result = st.session_state.get("demand_result")
    glass_start()
    if result:
        st.metric("Predicted Demand", result.get("predicted_demand", "N/A"), f"Confidence {result.get('confidence', 'N/A')}")
        st.info(f"Peak window: {result.get('peak_window', 'N/A')}")
        st.success(result.get("recommendation", "Demand forecast generated successfully."))
    else:
        st.metric("Predicted Demand", "Awaiting input", "Ready")
    glass_end()

    df = st.session_state.sensor_history.copy()
    glass_start()
    st.plotly_chart(line_chart(df, ["demand", "flow_rate"], "Demand vs Flow Trend"), use_container_width=True)
    glass_end()


def assets_alerts() -> None:
    section("🛠️ Assets & Alerts", "Asset health, maintenance priority, and live operational events.")
    assets_response = api_get("/assets")
    alerts_response = api_get("/alerts")
    assets = pd.DataFrame(assets_response["assets"]) if assets_response and "assets" in assets_response else asset_health()
    if alerts_response and "alerts" in alerts_response:
        merged_alerts = alerts_response["alerts"] + st.session_state.alerts
        st.session_state.alerts = merged_alerts[:8]

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Assets Online", f"{len(assets)}/{len(assets)}", "monitored", "▲ Connected", "📡")
    with c2:
        kpi_card("Avg Health", f"{assets['health'].mean():.0f}", "%", "▲ Maintenance forecast active", "🛠️")
    with c3:
        open_alerts = len([a for a in st.session_state.alerts if a["status"] != "Closed"])
        kpi_card("Open Alerts", open_alerts, "events", "Prioritized by severity", "🚦")

    st.dataframe(
        assets,
        use_container_width=True,
        hide_index=True,
        column_config={
            "health": st.column_config.ProgressColumn("Health", min_value=0, max_value=100),
            "runtime_hours": st.column_config.NumberColumn("Runtime Hours"),
        },
    )

    section("🚦 Live Alert Center", "Latest exceptions generated by simulated IoT signals.")
    alerts = pd.DataFrame(st.session_state.alerts)
    st.dataframe(alerts, use_container_width=True, hide_index=True)

    activity = api_get("/activity")
    if activity:
        section("Saved Platform Activity", "Recent AI results and operator actions stored for this city.")
        left, right = st.columns(2)
        with left:
            predictions = pd.DataFrame(activity.get("predictions", []))
            if not predictions.empty:
                st.dataframe(predictions, use_container_width=True, hide_index=True)
            else:
                status("No saved predictions yet.", "warning")
        with right:
            actions = pd.DataFrame(activity.get("control_actions", []))
            if not actions.empty:
                st.dataframe(actions, use_container_width=True, hide_index=True)
            else:
                status("No saved control actions yet.", "warning")


def automatic_alarms() -> None:
    section("Automatic Alarms", "Real-time harmful scenario detection from live water network signals.")
    st.warning("The system automatically checks for leakage, pressure danger, turbidity, pH, chlorine, and water loss risks.")

    test_col, log_col = st.columns((1, 1.4))
    with test_col:
        glass_start()
        st.subheader("Run Alarm Simulation")
        zone = st.selectbox("Zone", ["North Grid", "Central Grid", "Industrial East", "Residential West", "River Intake"])
        scenario = st.selectbox(
            "Scenario",
            ["Normal", "Leakage", "Pipe Burst", "High Pressure", "Unsafe Turbidity", "Bad pH", "Chemical Dose Issue"],
        )
        presets = {
            "Normal": {"flow_rate": 86, "pressure": 4.2, "turbidity": 2.1, "loss": 9, "ph": 7.2, "chlorine": 0.6, "vibration": 0.2, "acoustic_noise": 32},
            "Leakage": {"flow_rate": 126, "pressure": 2.2, "turbidity": 2.8, "loss": 24, "ph": 7.1, "chlorine": 0.6, "vibration": 0.5, "acoustic_noise": 46},
            "Pipe Burst": {"flow_rate": 142, "pressure": 2.0, "turbidity": 4.0, "loss": 29, "ph": 7.1, "chlorine": 0.6, "vibration": 0.95, "acoustic_noise": 68},
            "High Pressure": {"flow_rate": 90, "pressure": 6.8, "turbidity": 2.2, "loss": 10, "ph": 7.2, "chlorine": 0.6, "vibration": 0.2, "acoustic_noise": 32},
            "Unsafe Turbidity": {"flow_rate": 84, "pressure": 4.1, "turbidity": 8.2, "loss": 12, "ph": 7.3, "chlorine": 0.6, "vibration": 0.2, "acoustic_noise": 32},
            "Bad pH": {"flow_rate": 84, "pressure": 4.1, "turbidity": 2.4, "loss": 12, "ph": 9.1, "chlorine": 0.6, "vibration": 0.2, "acoustic_noise": 32},
            "Chemical Dose Issue": {"flow_rate": 84, "pressure": 4.1, "turbidity": 2.4, "loss": 12, "ph": 7.2, "chlorine": 1.4, "vibration": 0.2, "acoustic_noise": 32},
        }
        payload = {"zone": zone, **presets[scenario]}
        if st.button("Run Automatic Scan"):
            result = api_post("/monitoring/scan", payload)
            if result and result.get("alarm_count", 0) > 0:
                status(f"Alarm raised: {result.get('alarm_count')} issue detected.", "danger")
            else:
                status("No harmful scenario detected in this scan.", "safe")
        glass_end()

    with log_col:
        glass_start()
        st.subheader("Alarm Log")
        alerts_response = api_get("/alerts")
        alerts = pd.DataFrame(alerts_response.get("alerts", [])) if alerts_response else pd.DataFrame()
        if alerts.empty:
            status("No alarms stored yet.", "warning")
        else:
            st.dataframe(alerts, use_container_width=True, hide_index=True)
        glass_end()


def citizen_complaints() -> None:
    section("Citizen Complaints", "Submit and track city water service complaints from the logged-in account.")
    user = st.session_state.get("current_user", {})

    left, right = st.columns((1, 1.2))
    with left:
        glass_start()
        st.subheader("Submit Complaint")
        category = st.selectbox(
            "Issue Category",
            ["Water Leakage", "Low Pressure", "Water Quality", "No Water Supply", "Billing/Service", "Other"],
        )
        zone = st.selectbox(
            "Area / Zone",
            ["North Grid", "Central Grid", "Industrial East", "Residential West", "River Intake", "Hill Reservoir", "Other"],
        )
        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Emergency"], index=1)
        subject = st.text_input("Subject", placeholder="Example: Low pressure near sector 8")
        description = st.text_area("Description", placeholder="Describe the issue, location, timing, and visible impact.")

        if st.button("Submit Complaint"):
            result = api_post(
                "/complaints",
                {
                    "category": category,
                    "zone": zone,
                    "priority": priority,
                    "subject": subject,
                    "description": description,
                },
            )
            if result and result.get("complaint"):
                st.success("Complaint submitted successfully. Your city team can now track it.")
                st.rerun()
            else:
                st.error("Complaint could not be submitted. Please complete all required fields.")
        glass_end()

    with right:
        glass_start()
        st.subheader("Complaint Tracking")
        complaints_response = api_get("/complaints")
        complaints = pd.DataFrame(complaints_response.get("complaints", [])) if complaints_response else pd.DataFrame()
        if complaints.empty:
            status("No complaints submitted yet.", "warning")
        else:
            visible_columns = [
                "id",
                "category",
                "zone",
                "subject",
                "priority",
                "status",
                "response",
                "created_at",
            ]
            existing_columns = [column for column in visible_columns if column in complaints.columns]
            st.dataframe(complaints[existing_columns], use_container_width=True, hide_index=True)
        glass_end()

    if user.get("role") in {"admin", "operator"}:
        section("Operator Response", "Update citizen complaint status and add a service response.")
        complaints_response = api_get("/complaints")
        complaints = complaints_response.get("complaints", []) if complaints_response else []
        if complaints:
            complaint_options = {
                f"#{item['id']} - {item['subject']} ({item['status']})": item["id"]
                for item in complaints
            }
            selected_label = st.selectbox("Select Complaint", list(complaint_options.keys()))
            new_status = st.selectbox("New Status", ["Open", "In Progress", "Resolved", "Rejected"])
            response = st.text_area("Response to Citizen", placeholder="Add inspection notes or resolution message.")
            if st.button("Update Complaint Status"):
                complaint_id = complaint_options[selected_label]
                result = api_patch(
                    f"/complaints/{complaint_id}",
                    {"status": new_status, "response": response},
                )
                if result:
                    st.success("Complaint status updated.")
                    st.rerun()
                else:
                    st.error("Could not update complaint.")
        else:
            status("No citizen complaints waiting for review.", "safe")


def service_rating() -> None:
    section("Service Rating", "Share how you feel about the city water service experience.")
    user = st.session_state.get("current_user", {})
    left, right = st.columns((1, 1.2))

    with left:
        glass_start()
        st.subheader("Rate Your Experience")
        stars = st.slider("Stars", min_value=1, max_value=5, value=5)
        star_text = "★" * stars + "☆" * (5 - stars)
        st.markdown(f"### {star_text}")
        comment = st.text_area(
            "Optional Feedback",
            placeholder="Tell us what went well or what should improve.",
        )
        if st.button("Submit Rating"):
            result = api_post("/ratings", {"stars": stars, "comment": comment})
            if result and result.get("rating"):
                st.success("Thank you. Your rating has been submitted.")
                st.rerun()
            else:
                st.error("Rating could not be submitted. Please try again.")
        glass_end()

    with right:
        glass_start()
        st.subheader("Community Satisfaction")
        ratings_response = api_get("/ratings")
        summary = ratings_response.get("summary", {}) if ratings_response else {}
        average = float(summary.get("average", 0) or 0)
        total = int(summary.get("total", 0) or 0)
        st.metric("Average Rating", f"{average:.2f} / 5", f"{total} total ratings")
        gauge("Satisfaction score", average * 20)
        if average >= 4:
            status("Citizens are highly satisfied with the service experience.", "safe")
        elif average >= 3:
            status("Service sentiment is moderate. Improvement actions are recommended.", "warning")
        elif total > 0:
            status("Citizen sentiment is low. Immediate service review is recommended.", "danger")
        else:
            status("No ratings submitted yet.", "warning")
        glass_end()

    if user.get("role") in {"admin", "operator"}:
        section("Recent Feedback", "Latest citizen ratings and comments for the city team.")
        ratings_response = api_get("/ratings")
        ratings = pd.DataFrame(ratings_response.get("ratings", [])) if ratings_response else pd.DataFrame()
        if ratings.empty:
            status("No citizen feedback available yet.", "warning")
        else:
            visible_columns = ["id", "full_name", "email", "stars", "comment", "created_at"]
            existing_columns = [column for column in visible_columns if column in ratings.columns]
            st.dataframe(ratings[existing_columns], use_container_width=True, hide_index=True)


def water_system_control() -> None:
    section("Water System Control", "Supervisory control requests for smart-city water operations.")
    user = st.session_state.get("current_user", {})
    if user.get("role") not in {"admin", "operator"}:
        status("Only authorized city admins and operators can access system controls.", "danger")
        return

    st.warning(
        "Safety mode: these controls create audited requests only. Real pump or chemical actuation must be integrated and approved by certified water-system engineers."
    )

    limits = {
        "Flow Rate Setpoint": ("L/min", 20.0, 250.0, 95.0),
        "Pressure Setpoint": ("bar", 1.0, 8.0, 4.2),
        "pH Target": ("pH", 6.5, 8.5, 7.2),
        "Chlorine Dose": ("mg/L", 0.2, 1.0, 0.6),
        "Coagulant Dose": ("mg/L", 0.0, 60.0, 20.0),
    }

    left, right = st.columns((1, 1.2))
    with left:
        glass_start()
        st.subheader("Create Control Request")
        zone = st.selectbox(
            "City Zone",
            ["North Grid", "Central Grid", "Industrial East", "Residential West", "River Intake", "Hill Reservoir"],
        )
        control_type = st.selectbox("Control Type", list(limits.keys()))
        unit, minimum, maximum, default = limits[control_type]
        target_value = st.number_input(
            f"Target Value ({unit})",
            min_value=minimum,
            max_value=maximum,
            value=default,
            step=0.1,
        )
        reason = st.text_area(
            "Reason",
            placeholder="Example: Stabilize evening demand pressure in Residential West.",
        )
        safety_note = st.text_area(
            "Safety Note",
            value="Verify sensor readings and field conditions before execution.",
        )
        if st.button("Submit Control Request"):
            result = api_post(
                "/controls",
                {
                    "zone": zone,
                    "control_type": control_type,
                    "target_value": target_value,
                    "reason": reason,
                    "safety_note": safety_note,
                },
            )
            if result and result.get("control"):
                st.success("Control request submitted for review.")
                st.rerun()
            else:
                st.error("Control request could not be submitted.")
        glass_end()

    with right:
        glass_start()
        st.subheader("Control Request Log")
        controls_response = api_get("/controls")
        controls = pd.DataFrame(controls_response.get("controls", [])) if controls_response else pd.DataFrame()
        if controls.empty:
            status("No control requests yet.", "warning")
        else:
            visible_columns = [
                "id",
                "zone",
                "control_type",
                "target_value",
                "unit",
                "status",
                "full_name",
                "created_at",
            ]
            existing_columns = [column for column in visible_columns if column in controls.columns]
            st.dataframe(controls[existing_columns], use_container_width=True, hide_index=True)
        glass_end()

    if user.get("role") == "admin":
        section("Admin Approval", "Approve, reject, or mark control requests after operational review.")
        controls_response = api_get("/controls")
        controls = controls_response.get("controls", []) if controls_response else []
        if controls:
            control_options = {
                f"#{item['id']} - {item['control_type']} {item['target_value']} {item['unit']} ({item['status']})": item["id"]
                for item in controls
            }
            selected = st.selectbox("Select Control Request", list(control_options.keys()))
            new_status = st.selectbox("New Status", ["Pending Approval", "Approved", "Rejected", "Executed", "Cancelled"])
            if st.button("Update Control Status"):
                result = api_patch(
                    f"/controls/{control_options[selected]}",
                    {"status": new_status},
                )
                if result:
                    st.success("Control request status updated.")
                    st.rerun()
                else:
                    st.error("Could not update control request.")
        else:
            status("No control requests available for approval.", "safe")


def ai_control_room() -> None:
    section("🧠 AI Control Room", "Operational actions, optimization suggestions, and control audit trail.")
    left, right = st.columns((1, 1))

    with left:
        glass_start()
        st.subheader("Optimization Command")
        mode = st.selectbox("Strategy", ["Balanced", "Conservation First", "Pressure Stabilization", "Energy Saving"])
        target_zone = st.selectbox("Target Zone", ["All Zones", "North Grid", "Central Grid", "Industrial East", "Residential West"])
        automation = st.toggle("Enable supervised automation", value=False)
        if st.button("Generate Control Plan"):
            with st.spinner("Building AI control recommendation..."):
                time.sleep(1.1)
                result = post_with_fallback(
                    "/optimize",
                    {"strategy": mode, "zone": target_zone, "automation": automation},
                    optimize_fallback,
                )
            action = "Reduce pressure setpoint by 4% and rebalance pump schedule."
            if result:
                action = result.get("action", action)
            recommendation = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "mode": mode,
                "zone": target_zone,
                "automation": "Enabled" if automation else "Manual approval",
                "action": action,
            }
            st.session_state.control_log.insert(0, recommendation)
            st.session_state.control_log = st.session_state.control_log[:8]
            status("✅ Control recommendation generated and added to audit trail.", "safe")
            if result:
                st.info(result.get("action", "Control recommendation generated successfully."))
        glass_end()

    with right:
        glass_start()
        st.subheader("AI Recommendations")
        status("🧭 Shift non-critical pumping to off-peak energy window.", "warning")
        status("💧 Prioritize Industrial East for leak inspection sweep.", "danger")
        status("✅ Maintain current reservoir release schedule for next 6 hours.", "safe")
        glass_end()

    if st.session_state.control_log:
        st.dataframe(pd.DataFrame(st.session_state.control_log), use_container_width=True, hide_index=True)
    else:
        status("No control actions generated yet.", "warning")


def render_footer() -> None:
    st.markdown(
        f'<div class="footer">Aqua Sentinel AI • Developer: {DEVELOPER_NAME} • Smart water conservation platform</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    initialize_state()
    if not st.session_state.get("auth_token"):
        render_auth_screen()
        render_footer()
        return
    selected = render_sidebar()
    hero()

    if selected == "Command Center":
        if hasattr(st, "fragment"):
            @st.fragment(run_every=f"{REFRESH_SECONDS}s")
            def live_fragment() -> None:
                command_center()

            live_fragment()
        else:
            command_center()
            st.info("Upgrade Streamlit to enable native timed auto-refresh.")
    elif selected == "My Water Account":
        my_water_account()
    elif selected == "Leakage Detection":
        leakage_detection()
    elif selected == "Water Quality":
        water_quality()
    elif selected == "Demand Prediction":
        demand_prediction()
    elif selected == "Assets & Alerts":
        assets_alerts()
    elif selected == "Automatic Alarms":
        automatic_alarms()
    elif selected == "Citizen Complaints":
        citizen_complaints()
    elif selected == "Service Rating":
        service_rating()
    elif selected == "Water System Control":
        water_system_control()
    else:
        ai_control_room()

    render_footer()


if __name__ == "__main__":
    main()
