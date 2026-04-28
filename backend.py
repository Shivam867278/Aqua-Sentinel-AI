from __future__ import annotations

import math
import random
import logging
import json
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Dict

from flask import Flask, request
from flask_cors import CORS

from config import settings
from database import (
    authenticate_user,
    create_alert,
    create_complaint,
    create_rating,
    create_system_control,
    create_user,
    get_user_by_token,
    get_citizen_water_account,
    init_db,
    list_complaints,
    list_alerts,
    list_ratings,
    list_saved_activity,
    list_system_controls,
    save_control_action,
    save_prediction,
    update_system_control_status,
    update_complaint_status,
)
from response_utils import error_response, success_response
from validation import parse_float, validate_choice, validate_range


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("aqua-sentinel-api")

app = Flask(__name__)
CORS(app, origins=settings.cors_origins)
init_db()


def as_float(payload: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def current_user() -> Dict[str, Any] | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.replace("Bearer ", "", 1).strip()
    if not token:
        return None
    return get_user_by_token(token)


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if user is None:
            return error_response("Login required", 401)
        request.current_user = user
        return view(*args, **kwargs)

    return wrapped


@app.errorhandler(404)
def not_found(_error):
    return error_response("Endpoint not found", 404)


@app.errorhandler(500)
def internal_error(error):
    logger.exception("Unhandled API error: %s", error)
    return error_response("Internal server error", 500)


@app.get("/")
def index():
    return success_response(
        {
            "service": "Aqua Sentinel AI Flask API",
            "status": "online",
            "environment": settings.environment,
            "endpoints": [
                "/auth/login",
                "/auth/register",
                "/auth/me",
                "/health",
                "/telemetry",
                "/assets",
                "/alerts",
                "/activity",
                "/complaints",
                "/ratings",
                "/controls",
                "/citizen/water-account",
                "/leakage",
                "/quality",
                "/predict-demand",
                "/optimize",
            ],
        }
    )


@app.get("/health")
def health():
    return success_response({"status": "ok", "service": settings.app_name})


@app.post("/auth/login")
def login():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not email or not password:
        return error_response("Email and password are required", 400)
    auth = authenticate_user(email, password)
    if auth is None:
        return error_response("Invalid email or password", 401)
    return success_response(auth, "Login successful")


@app.post("/auth/register")
def register():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)
    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    city_name = str(payload.get("city_name", "Smart Water City")).strip() or "Smart Water City"
    if not full_name or not email or not password:
        return error_response("Full name, email, and password are required", 400)
    if len(password) < 6:
        return error_response("Password must be at least 6 characters", 400)
    try:
        auth = create_user(full_name, email, password, city_name, "citizen")
    except Exception:
        logger.exception("Registration failed")
        return error_response("Could not create account. The email may already be registered.", 400)
    return success_response(auth, "Account created", 201)


@app.get("/auth/me")
@login_required
def me():
    return success_response({"user": request.current_user})


@app.get("/telemetry")
def telemetry():
    now = datetime.utcnow()
    points = []
    flow = random.uniform(78, 96)
    pressure = random.uniform(3.2, 4.7)
    demand = random.uniform(1080, 1450)
    for index in range(36):
        points.append(
            {
                "time": (now - timedelta(seconds=(35 - index) * 5)).isoformat() + "Z",
                "flow_rate": round(flow + random.uniform(-5, 5), 2),
                "pressure": round(pressure + random.uniform(-0.35, 0.35), 2),
                "demand": round(demand + random.uniform(-110, 110), 2),
                "turbidity": round(random.uniform(1.2, 4.2), 2),
                "energy": round(random.uniform(58, 92), 2),
                "loss": round(random.uniform(6, 17), 2),
            }
        )
    return success_response({"points": points})


@app.get("/assets")
def assets():
    asset_rows = [
        ("PMP-101", "North Lift Pump", "North Grid", "Pump"),
        ("VAL-204", "Central Pressure Valve", "Central Grid", "Valve"),
        ("TNK-302", "Hill Storage Tank", "Hill Reservoir", "Tank"),
        ("MTR-118", "Industrial Bulk Meter", "Industrial East", "Meter"),
        ("SNS-417", "River Quality Sensor", "River Intake", "Sensor"),
        ("PMP-226", "West Booster Pump", "Residential West", "Pump"),
    ]
    return success_response(
        {
            "assets": [
                {
                    "asset_id": asset_id,
                    "name": name,
                    "zone": zone,
                    "type": asset_type,
                    "health": random.randint(74, 98),
                    "runtime_hours": random.randint(900, 13000),
                    "status": random.choice(["Online", "Online", "Online", "Maintenance Due"]),
                }
                for asset_id, name, zone, asset_type in asset_rows
            ]
        }
    )


@app.get("/alerts")
def alerts():
    user = current_user()
    if user:
        return success_response({"alerts": list_alerts(user["city_id"])})
    return success_response({"alerts": list_alerts(1)})


@app.get("/activity")
@login_required
def activity():
    return success_response(list_saved_activity(request.current_user["city_id"]))


@app.get("/complaints")
@login_required
def complaints():
    return success_response({"complaints": list_complaints(request.current_user)})


@app.post("/complaints")
@login_required
def submit_complaint():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)

    category = str(payload.get("category", "")).strip()
    zone = str(payload.get("zone", "")).strip()
    subject = str(payload.get("subject", "")).strip()
    description = str(payload.get("description", "")).strip()
    priority = str(payload.get("priority", "Medium")).strip()

    if not category or not zone or not subject or not description:
        return error_response("Category, zone, subject, and description are required", 400)
    try:
        validate_choice(priority, "priority", ["Low", "Medium", "High", "Emergency"])
    except ValueError as exc:
        return error_response(str(exc), 400)

    complaint = create_complaint(
        request.current_user["id"],
        request.current_user["city_id"],
        category,
        zone,
        subject,
        description,
        priority,
    )
    return success_response({"complaint": complaint}, "Complaint submitted", 201)


@app.patch("/complaints/<int:complaint_id>")
@login_required
def update_complaint(complaint_id: int):
    user = request.current_user
    if user["role"] not in {"admin", "operator"}:
        return error_response("Only city admins and operators can update complaints", 403)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)
    status = str(payload.get("status", "")).strip()
    response = str(payload.get("response", "")).strip()
    try:
        validate_choice(status, "status", ["Open", "In Progress", "Resolved", "Rejected"])
    except ValueError as exc:
        return error_response(str(exc), 400)

    complaint = update_complaint_status(complaint_id, user["city_id"], status, response)
    if complaint is None:
        return error_response("Complaint not found", 404)
    return success_response({"complaint": complaint}, "Complaint updated")


@app.get("/ratings")
@login_required
def ratings():
    return success_response(list_ratings(request.current_user["city_id"]))


@app.post("/ratings")
@login_required
def submit_rating():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)
    try:
        stars = int(payload.get("stars", 0))
        validate_range(stars, "stars", (1, 5))
    except (TypeError, ValueError) as exc:
        return error_response(str(exc), 400)
    comment = str(payload.get("comment", "")).strip()
    rating = create_rating(
        request.current_user["id"],
        request.current_user["city_id"],
        stars,
        comment,
    )
    return success_response({"rating": rating}, "Rating submitted", 201)


@app.get("/citizen/water-account")
@login_required
def citizen_water_account():
    return success_response(get_citizen_water_account(request.current_user))


CONTROL_LIMITS = {
    "Flow Rate Setpoint": {"unit": "L/min", "min": 20.0, "max": 250.0},
    "Pressure Setpoint": {"unit": "bar", "min": 1.0, "max": 8.0},
    "pH Target": {"unit": "pH", "min": 6.5, "max": 8.5},
    "Chlorine Dose": {"unit": "mg/L", "min": 0.2, "max": 1.0},
    "Coagulant Dose": {"unit": "mg/L", "min": 0.0, "max": 60.0},
}


def evaluate_alarm_rules(payload: Dict[str, Any]) -> list[Dict[str, Any]]:
    zone = str(payload.get("zone", "Unknown Zone"))
    flow_rate = as_float(payload, "flow_rate", 80.0)
    pressure = as_float(payload, "pressure", 4.0)
    turbidity = as_float(payload, "turbidity", 2.0)
    loss = as_float(payload, "loss", 10.0)
    ph = as_float(payload, "ph", 7.2)
    chlorine = as_float(payload, "chlorine", 0.6)
    vibration = as_float(payload, "vibration", 0.2)
    acoustic_noise = as_float(payload, "acoustic_noise", 32.0)

    alarms = []
    if flow_rate > 115 and pressure < 2.8:
        alarms.append({"severity": "High", "zone": zone, "event": "Probable leakage: high flow with pressure drop"})
    if vibration > 0.75 or acoustic_noise > 55:
        alarms.append({"severity": "High", "zone": zone, "event": "Possible pipe burst/leakage acoustic signature"})
    if pressure > 6.2:
        alarms.append({"severity": "High", "zone": zone, "event": "Dangerous pressure level detected"})
    if turbidity > 6.0:
        alarms.append({"severity": "High", "zone": zone, "event": "Water quality alarm: turbidity is unsafe"})
    if loss > 20:
        alarms.append({"severity": "Medium", "zone": zone, "event": "High non-revenue water loss detected"})
    if ph < 6.5 or ph > 8.5:
        alarms.append({"severity": "High", "zone": zone, "event": "Water quality alarm: pH outside safe range"})
    if chlorine < 0.2 or chlorine > 1.0:
        alarms.append({"severity": "Medium", "zone": zone, "event": "Chemical dosing alarm: chlorine outside target range"})
    return alarms


@app.post("/monitoring/scan")
def monitoring_scan():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)

    user = current_user()
    city_id = user["city_id"] if user else 1
    alarms = evaluate_alarm_rules(payload)
    stored_alerts = [
        create_alert(city_id, alarm["severity"], alarm["zone"], alarm["event"])
        for alarm in alarms
    ]
    status_label = "danger" if stored_alerts else "safe"
    return success_response(
        {
            "status": status_label,
            "alarm_count": len(stored_alerts),
            "alarms": stored_alerts,
            "message": (
                "Automatic alarm raised. Operator attention required."
                if stored_alerts
                else "No harmful scenario detected."
            ),
        }
    )


@app.get("/controls")
@login_required
def controls():
    user = request.current_user
    if user["role"] not in {"admin", "operator"}:
        return error_response("Only city admins and operators can view control requests", 403)
    return success_response({"controls": list_system_controls(user["city_id"])})


@app.post("/controls")
@login_required
def create_control():
    user = request.current_user
    if user["role"] not in {"admin", "operator"}:
        return error_response("Only city admins and operators can create control requests", 403)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)

    zone = str(payload.get("zone", "")).strip()
    control_type = str(payload.get("control_type", "")).strip()
    reason = str(payload.get("reason", "")).strip()
    safety_note = str(payload.get("safety_note", "")).strip()
    if not zone or not control_type or not reason:
        return error_response("Zone, control type, and reason are required", 400)
    if control_type not in CONTROL_LIMITS:
        return error_response("Unsupported control type", 400)

    try:
        target_value = float(payload.get("target_value"))
    except (TypeError, ValueError):
        return error_response("Target value must be a number", 400)

    limits = CONTROL_LIMITS[control_type]
    try:
        validate_range(target_value, "target_value", (limits["min"], limits["max"]))
    except ValueError as exc:
        return error_response(str(exc), 400)

    control = create_system_control(
        user["id"],
        user["city_id"],
        zone,
        control_type,
        target_value,
        limits["unit"],
        reason,
        safety_note or "Requires trained operator approval before field execution.",
    )
    return success_response({"control": control}, "Control request created", 201)


@app.patch("/controls/<int:control_id>")
@login_required
def update_control(control_id: int):
    user = request.current_user
    if user["role"] != "admin":
        return error_response("Only city admins can approve or reject control requests", 403)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)
    status = str(payload.get("status", "")).strip()
    try:
        validate_choice(status, "status", ["Pending Approval", "Approved", "Rejected", "Executed", "Cancelled"])
    except ValueError as exc:
        return error_response(str(exc), 400)

    control = update_system_control_status(control_id, user["city_id"], user["id"], status)
    if control is None:
        return error_response("Control request not found", 404)
    return success_response({"control": control}, "Control request updated")


@app.post("/optimize")
def optimize():
    payload = request.get_json(silent=True) or {}
    strategy = payload.get("strategy", "Balanced")
    zone = payload.get("zone", "All Zones")
    try:
        validate_choice(strategy, "strategy", ["Balanced", "Conservation First", "Pressure Stabilization", "Energy Saving"])
    except ValueError as exc:
        return error_response(str(exc), 400)
    result = {
            "strategy": strategy,
            "zone": zone,
            "estimated_savings": f"{random.uniform(6.5, 14.8):.1f}%",
            "action": "Rebalance pump schedule, reduce pressure setpoint, and prioritize leak inspection route.",
            "approval_required": True,
            "confidence": round(random.uniform(0.86, 0.96), 2),
        }
    user = current_user()
    if user:
        save_control_action(user["id"], user["city_id"], strategy, zone, result["action"])
    return success_response(result)


@app.post("/leakage")
def leakage():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)

    try:
        flow_rate = parse_float(payload, "flow_rate", 80.0)
        pressure = parse_float(payload, "pressure", 4.0)
        vibration = parse_float(payload, "vibration", 0.2)
        acoustic_noise = parse_float(payload, "acoustic_noise", 32.0)
        validate_range(flow_rate, "flow_rate", (0, 500))
        validate_range(pressure, "pressure", (0, 20))
        validate_range(vibration, "vibration", (0, 10))
        validate_range(acoustic_noise, "acoustic_noise", (0, 160))
    except ValueError as exc:
        return error_response(str(exc), 400)
    zone = payload.get("zone", "Unknown")

    pressure_drop_risk = clamp((3.2 - pressure) / 2.2, 0, 1)
    abnormal_flow_risk = clamp((flow_rate - 95) / 45, 0, 1)
    vibration_risk = clamp((vibration - 0.45) / 0.75, 0, 1)
    acoustic_risk = clamp((acoustic_noise - 42) / 28, 0, 1)

    risk_score = (
        pressure_drop_risk * 0.28
        + abnormal_flow_risk * 0.24
        + vibration_risk * 0.24
        + acoustic_risk * 0.24
    )
    risk_score = clamp(risk_score + random.uniform(-0.03, 0.03), 0, 1)
    leak_detected = risk_score >= 0.52

    result = {
            "leak_detected": leak_detected,
            "status": "danger" if leak_detected else "safe",
            "confidence": round((0.72 + risk_score * 0.24) if leak_detected else (0.84 - risk_score * 0.18), 2),
            "risk_score": round(risk_score, 3),
            "zone": zone,
            "recommendation": (
                "Dispatch inspection crew and isolate the suspected zone."
                if leak_detected
                else "Continue live monitoring. No leak signature detected."
            ),
        }
    user = current_user()
    if user:
        save_prediction(user["id"], user["city_id"], "leakage", json.dumps(payload), json.dumps(result))
    return success_response(result)


@app.post("/quality")
def quality():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)

    try:
        ph = parse_float(payload, "ph", 7.2)
        turbidity = parse_float(payload, "turbidity", 2.0)
        tds = parse_float(payload, "tds", 320.0)
        temperature = parse_float(payload, "temperature", 24.0)
        chlorine = parse_float(payload, "chlorine", 0.6)
        conductivity = parse_float(payload, "conductivity", 500.0)
        validate_range(ph, "ph", (0, 14))
        validate_range(turbidity, "turbidity", (0, 100))
        validate_range(tds, "tds", (0, 5000))
        validate_range(temperature, "temperature", (-5, 80))
        validate_range(chlorine, "chlorine", (0, 10))
        validate_range(conductivity, "conductivity", (0, 10000))
    except ValueError as exc:
        return error_response(str(exc), 400)

    ph_risk = 0 if 6.5 <= ph <= 8.5 else min(abs(ph - 7.4) / 4.2, 1)
    turbidity_risk = clamp((turbidity - 4.5) / 8.0, 0, 1)
    tds_risk = clamp((tds - 500) / 600, 0, 1)
    chlorine_risk = 0 if 0.2 <= chlorine <= 1.0 else min(abs(chlorine - 0.6) / 1.2, 1)
    conductivity_risk = clamp((conductivity - 900) / 900, 0, 1)
    temperature_risk = clamp((temperature - 34) / 12, 0, 1)

    risk_score = clamp(
        ph_risk * 0.2
        + turbidity_risk * 0.24
        + tds_risk * 0.18
        + chlorine_risk * 0.18
        + conductivity_risk * 0.12
        + temperature_risk * 0.08,
        0,
        1,
    )

    unsafe = risk_score >= 0.45
    quality_label = "Unsafe" if unsafe else "Good"

    result = {
            "quality": quality_label,
            "status": "danger" if unsafe else "safe",
            "unsafe": unsafe,
            "quality_score": round((1 - risk_score) * 100, 1),
            "risk_score": round(risk_score, 3),
            "recommendation": (
                "Trigger treatment review and increase sampling frequency."
                if unsafe
                else "Water quality is inside normal operating thresholds."
            ),
        }
    user = current_user()
    if user:
        save_prediction(user["id"], user["city_id"], "quality", json.dumps(payload), json.dumps(result))
    return success_response(result)


@app.post("/predict-demand")
def predict_demand():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be valid JSON", 400)

    try:
        population = parse_float(payload, "population", 12500)
        avg_temperature = parse_float(payload, "avg_temperature", 29)
        rainfall = parse_float(payload, "rainfall", 3)
        day_type = str(payload.get("day_type", "Weekday"))
        industrial_load = parse_float(payload, "industrial_load", 62)
        current_storage = parse_float(payload, "current_storage", 74)
        validate_range(population, "population", (1, 100000000))
        validate_range(avg_temperature, "avg_temperature", (-20, 60))
        validate_range(rainfall, "rainfall", (0, 1000))
        validate_choice(day_type, "day_type", ["Weekday", "Weekend", "Holiday"])
        validate_range(industrial_load, "industrial_load", (0, 100))
        validate_range(current_storage, "current_storage", (0, 100))
    except ValueError as exc:
        return error_response(str(exc), 400)

    base = population * 135
    temperature_factor = 1 + clamp((avg_temperature - 24) / 55, -0.12, 0.22)
    rainfall_factor = 1 - clamp(rainfall / 140, 0, 0.18)
    day_factor = {"Weekday": 1.0, "Weekend": 0.93, "Holiday": 0.88}.get(day_type, 1.0)
    industrial_factor = 1 + industrial_load / 500
    storage_factor = 1 + clamp((55 - current_storage) / 300, -0.05, 0.12)
    seasonal_wave = 1 + math.sin(datetime.now().timetuple().tm_yday / 365 * math.tau) * 0.04

    predicted_liters = base * temperature_factor * rainfall_factor * day_factor * industrial_factor * storage_factor * seasonal_wave
    predicted_liters *= random.uniform(0.985, 1.015)

    result = {
            "predicted_demand": f"{predicted_liters:,.0f} L/day",
            "predicted_liters": round(predicted_liters, 2),
            "confidence": round(random.uniform(0.86, 0.95), 2),
            "peak_window": "06:00-09:00 and 18:00-21:00",
            "recommendation": (
                "Prepare demand response and review reservoir release schedule."
                if current_storage < 45
                else "Current storage is adequate for the predicted demand profile."
            ),
        }
    user = current_user()
    if user:
        save_prediction(user["id"], user["city_id"], "demand", json.dumps(payload), json.dumps(result))
    return success_response(result)


if __name__ == "__main__":
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.environment == "development",
    )
