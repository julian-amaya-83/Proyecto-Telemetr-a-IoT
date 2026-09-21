from pathlib import Path

from fastapi.testclient import TestClient

import backend.database as database
from backend.main import app

TEST_DB = Path(__file__).resolve().parents[1] / "database" / "test_iot.db"


def payload(message_id="HYD-001-TEST-000001", device_id="HYD-001"):
    return {
        "message_id": message_id,
        "device_id": device_id,
        "timestamp": "2026-09-21T04:00:00Z",
        "sequence": 1,
        "measurements": {
            "flow_l_min": 2.4,
            "pressure_kpa": 180.5,
            "consumption_valve_open": True,
        },
    }


def use_test_database(monkeypatch):
    if TEST_DB.exists():
        TEST_DB.unlink()
    monkeypatch.setattr(database, "DB_PATH", TEST_DB)


def test_health_and_registered_devices(monkeypatch):
    use_test_database(monkeypatch)
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        with database.get_connection() as connection:
            devices = connection.execute(
                "SELECT device_id, expected_interval_seconds FROM devices ORDER BY device_id"
            ).fetchall()
    assert [(row["device_id"], row["expected_interval_seconds"]) for row in devices] == [
        ("HYD-001", 5), ("HYD-002", 10), ("HYD-003", 3), ("HYD-004", 7)
    ]


def test_valid_telemetry_is_persisted(monkeypatch):
    use_test_database(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/api/telemetry", json=payload())
        assert response.status_code == 201
        with database.get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM telemetry WHERE message_id = ?", ("HYD-001-TEST-000001",)
            ).fetchone()
            device = connection.execute(
                "SELECT last_seen_at FROM devices WHERE device_id = 'HYD-001'"
            ).fetchone()
    assert row["flow_l_min"] == 2.4
    assert row["pressure_kpa"] == 180.5
    assert row["consumption_valve_open"] == 1
    assert device["last_seen_at"] is not None


def test_duplicate_returns_409(monkeypatch):
    use_test_database(monkeypatch)
    with TestClient(app) as client:
        assert client.post("/api/telemetry", json=payload()).status_code == 201
        assert client.post("/api/telemetry", json=payload()).status_code == 409


def test_unknown_device_returns_404(monkeypatch):
    use_test_database(monkeypatch)
    with TestClient(app) as client:
        response = client.post("/api/telemetry", json=payload(device_id="HYD-999"))
    assert response.status_code == 404


def test_invalid_domain_values_return_422(monkeypatch):
    use_test_database(monkeypatch)
    invalid = payload()
    invalid["measurements"]["pressure_kpa"] = 500
    with TestClient(app) as client:
        response = client.post("/api/telemetry", json=invalid)
    assert response.status_code == 422


def test_string_measurement_is_not_coerced(monkeypatch):
    use_test_database(monkeypatch)
    invalid = payload()
    invalid["measurements"]["flow_l_min"] = "2.4"
    with TestClient(app) as client:
        response = client.post("/api/telemetry", json=invalid)
    assert response.status_code == 422


def test_database_survives_reinitialization(monkeypatch):
    use_test_database(monkeypatch)
    with TestClient(app) as client:
        assert client.post("/api/telemetry", json=payload()).status_code == 201
    database.init_db()
    with database.get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
    assert count == 1
