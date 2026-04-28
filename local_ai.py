from __future__ import annotations

import math
import random
from datetime import datetime
from typing import Any, Dict


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def as_float(payload: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(payload.get(key, default))
    except (TypeError, ValueError):
        return default


def leakage_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
    flow_rate = as_float(payload, "flow_rate", 80.0)
    pressure = as_float(payload, "pressure", 4.0)
    vibration = as_float(payload, "vibration", 0.2)
    acoustic_noise = as_float(payload, "acoustic_noise", 32.0)

    pressure_drop_risk = clamp((3.2 - pressure) / 2.2, 0, 1)
    abnormal_flow_risk = clamp((flow_rate - 95) / 45, 0, 1)
    vibration_risk = clamp((vibration - 0.45) / 0.75, 0, 1)
    acoustic_risk = clamp((acoustic_noise - 42) / 28, 0, 1)

    risk_score = clamp(
        pressure_drop_risk * 0.28
        + abnormal_flow_risk * 0.24
        + vibration_risk * 0.24
        + acoustic_risk * 0.24
        + random.uniform(-0.02, 0.02),
        0,
        1,
    )
    leak_detected = risk_score >= 0.52
    return {
        "source": "local simulation fallback",
        "leak_detected": leak_detected,
        "status": "danger" if leak_detected else "safe",
        "confidence": round((0.72 + risk_score * 0.24) if leak_detected else (0.84 - risk_score * 0.18), 2),
        "risk_score": round(risk_score, 3),
        "zone": payload.get("zone", "Unknown"),
        "recommendation": (
            "Dispatch inspection crew and isolate the suspected zone."
            if leak_detected
            else "Continue monitoring. No leak signature detected."
        ),
    }


def quality_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
    ph = as_float(payload, "ph", 7.2)
    turbidity = as_float(payload, "turbidity", 2.0)
    tds = as_float(payload, "tds", 320.0)
    temperature = as_float(payload, "temperature", 24.0)
    chlorine = as_float(payload, "chlorine", 0.6)
    conductivity = as_float(payload, "conductivity", 500.0)

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
    return {
        "source": "local simulation fallback",
        "quality": "Unsafe" if unsafe else "Good",
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


def demand_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
    population = as_float(payload, "population", 12500)
    avg_temperature = as_float(payload, "avg_temperature", 29)
    rainfall = as_float(payload, "rainfall", 3)
    day_type = str(payload.get("day_type", "Weekday"))
    industrial_load = as_float(payload, "industrial_load", 62)
    current_storage = as_float(payload, "current_storage", 74)

    base = population * 135
    temperature_factor = 1 + clamp((avg_temperature - 24) / 55, -0.12, 0.22)
    rainfall_factor = 1 - clamp(rainfall / 140, 0, 0.18)
    day_factor = {"Weekday": 1.0, "Weekend": 0.93, "Holiday": 0.88}.get(day_type, 1.0)
    industrial_factor = 1 + industrial_load / 500
    storage_factor = 1 + clamp((55 - current_storage) / 300, -0.05, 0.12)
    seasonal_wave = 1 + math.sin(datetime.now().timetuple().tm_yday / 365 * math.tau) * 0.04
    predicted_liters = (
        base
        * temperature_factor
        * rainfall_factor
        * day_factor
        * industrial_factor
        * storage_factor
        * seasonal_wave
        * random.uniform(0.985, 1.015)
    )

    return {
        "source": "local simulation fallback",
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


def optimize_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source": "local simulation fallback",
        "strategy": payload.get("strategy", "Balanced"),
        "zone": payload.get("zone", "All Zones"),
        "estimated_savings": f"{random.uniform(6.5, 14.8):.1f}%",
        "action": "Rebalance pump schedule, reduce pressure setpoint, and prioritize leak inspection route.",
        "approval_required": True,
        "confidence": round(random.uniform(0.86, 0.96), 2),
    }
