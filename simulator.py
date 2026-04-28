import random
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import streamlit as st


REFRESH_SECONDS = 3


ZONES = [
    "North Grid",
    "Central Grid",
    "Industrial East",
    "Residential West",
    "River Intake",
    "Hill Reservoir",
]


ASSETS = [
    {"asset_id": "PMP-101", "name": "North Lift Pump", "zone": "North Grid", "type": "Pump"},
    {"asset_id": "VAL-204", "name": "Central Pressure Valve", "zone": "Central Grid", "type": "Valve"},
    {"asset_id": "TNK-302", "name": "Hill Storage Tank", "zone": "Hill Reservoir", "type": "Tank"},
    {"asset_id": "MTR-118", "name": "Industrial Bulk Meter", "zone": "Industrial East", "type": "Meter"},
    {"asset_id": "SNS-417", "name": "River Quality Sensor", "zone": "River Intake", "type": "Sensor"},
    {"asset_id": "PMP-226", "name": "West Booster Pump", "zone": "Residential West", "type": "Pump"},
]


def initialize_state() -> None:
    if "sensor_history" not in st.session_state:
        now = datetime.now()
        rows = []
        for i in range(42, 0, -1):
            rows.append(
                {
                    "time": now - timedelta(seconds=i * REFRESH_SECONDS),
                    "flow_rate": round(random.uniform(72, 96), 2),
                    "pressure": round(random.uniform(3.1, 4.8), 2),
                    "demand": round(random.uniform(1050, 1420), 2),
                    "turbidity": round(random.uniform(1.1, 3.8), 2),
                    "energy": round(random.uniform(62, 86), 2),
                    "loss": round(random.uniform(7, 15), 2),
                }
            )
        st.session_state.sensor_history = pd.DataFrame(rows)

    if "alerts" not in st.session_state:
        st.session_state.alerts = seed_alerts()

    if "control_log" not in st.session_state:
        st.session_state.control_log = []


def seed_alerts() -> List[Dict[str, str]]:
    return [
        {
            "time": (datetime.now() - timedelta(minutes=22)).strftime("%H:%M"),
            "severity": "High",
            "zone": "Industrial East",
            "event": "Pressure deviation near bulk meter",
            "status": "Investigating",
        },
        {
            "time": (datetime.now() - timedelta(minutes=47)).strftime("%H:%M"),
            "severity": "Medium",
            "zone": "River Intake",
            "event": "Turbidity increased above normal baseline",
            "status": "Open",
        },
        {
            "time": (datetime.now() - timedelta(hours=2)).strftime("%H:%M"),
            "severity": "Low",
            "zone": "Residential West",
            "event": "Demand spike resolved automatically",
            "status": "Closed",
        },
    ]


def simulate_sensor_tick() -> Dict[str, float]:
    previous = st.session_state.sensor_history.iloc[-1]
    flow = max(42, min(132, previous["flow_rate"] + random.uniform(-4.5, 4.5)))
    pressure = max(1.1, min(6.9, previous["pressure"] + random.uniform(-0.24, 0.24)))
    demand = max(720, min(1850, previous["demand"] + random.uniform(-80, 80)))
    turbidity = max(0.4, min(8.8, previous["turbidity"] + random.uniform(-0.35, 0.35)))
    energy = max(48, min(104, previous["energy"] + random.uniform(-3.0, 3.0)))
    loss = max(3, min(28, previous["loss"] + random.uniform(-1.2, 1.2)))

    new_row = pd.DataFrame(
        [
            {
                "time": datetime.now(),
                "flow_rate": round(flow, 2),
                "pressure": round(pressure, 2),
                "demand": round(demand, 2),
                "turbidity": round(turbidity, 2),
                "energy": round(energy, 2),
                "loss": round(loss, 2),
            }
        ]
    )
    st.session_state.sensor_history = pd.concat(
        [st.session_state.sensor_history, new_row], ignore_index=True
    ).tail(72)

    if pressure > 5.8 or turbidity > 6.4 or loss > 20:
        event = "Hydraulic anomaly detected"
        if turbidity > 6.4:
            event = "Water quality threshold exceeded"
        elif loss > 20:
            event = "Non-revenue water loss elevated"
        st.session_state.alerts.insert(
            0,
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "severity": "High" if pressure > 6 or turbidity > 7 else "Medium",
                "zone": random.choice(ZONES),
                "event": event,
                "status": "Open",
            },
        )
        st.session_state.alerts = st.session_state.alerts[:8]

    return {
        "flow_rate": round(flow, 2),
        "pressure": round(pressure, 2),
        "demand": round(demand, 2),
        "turbidity": round(turbidity, 2),
        "energy": round(energy, 2),
        "loss": round(loss, 2),
    }


def asset_health() -> pd.DataFrame:
    rows = []
    for asset in ASSETS:
        base_health = random.randint(74, 98)
        risk = "Low"
        if base_health < 82:
            risk = "Medium"
        if base_health < 76:
            risk = "High"
        rows.append(
            {
                **asset,
                "health": base_health,
                "risk": risk,
                "runtime_hours": random.randint(920, 12840),
                "next_service": (datetime.now() + timedelta(days=random.randint(7, 96))).strftime("%d %b %Y"),
            }
        )
    return pd.DataFrame(rows)


def zone_snapshot() -> pd.DataFrame:
    rows = []
    for zone in ZONES:
        rows.append(
            {
                "zone": zone,
                "flow_rate": round(random.uniform(62, 128), 1),
                "pressure": round(random.uniform(2.4, 6.2), 2),
                "quality": random.choice(["Good", "Good", "Good", "Watch"]),
                "loss_percent": round(random.uniform(5, 22), 1),
                "status": random.choice(["Stable", "Stable", "Stable", "Attention"]),
            }
        )
    return pd.DataFrame(rows)
