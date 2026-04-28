from backend import app


def test_health_endpoint():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_leakage_endpoint_returns_prediction():
    client = app.test_client()
    response = client.post(
        "/leakage",
        json={
            "flow_rate": 82.5,
            "pressure": 4.1,
            "vibration": 0.28,
            "acoustic_noise": 34.0,
            "zone": "North Grid",
        },
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert "leak_detected" in body["data"]
    assert "risk_score" in body["data"]


def test_quality_rejects_invalid_range():
    client = app.test_client()
    response = client.post(
        "/quality",
        json={
            "ph": 30,
            "turbidity": 2.1,
            "tds": 320,
            "temperature": 24.5,
            "chlorine": 0.6,
            "conductivity": 510,
        },
    )
    assert response.status_code == 400
    body = response.get_json()
    assert body["success"] is False
