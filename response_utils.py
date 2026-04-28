from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from flask import jsonify


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def success_response(data: Dict[str, Any], message: str = "ok", status_code: int = 200):
    body = {
        "success": True,
        "message": message,
        "data": data,
        "request_id": str(uuid4()),
        "timestamp": now_iso(),
    }
    return jsonify(body), status_code


def error_response(
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None,
):
    body = {
        "success": False,
        "message": message,
        "details": details or {},
        "request_id": str(uuid4()),
        "timestamp": now_iso(),
    }
    return jsonify(body), status_code


def unwrap_payload(response_json: Dict[str, Any]) -> Dict[str, Any]:
    if response_json.get("success") is True and isinstance(response_json.get("data"), dict):
        return response_json["data"]
    return response_json
