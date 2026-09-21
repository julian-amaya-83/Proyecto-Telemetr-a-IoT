"""Persistencia SQLite para dispositivos y telemetría hidráulica."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from backend.schemas import TelemetryIn

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "database" / "iot.db"


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                expected_interval_seconds INTEGER NOT NULL CHECK(expected_interval_seconds > 0),
                enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0, 1)),
                created_at TEXT NOT NULL,
                last_seen_at TEXT
            );

            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL UNIQUE,
                device_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                received_at TEXT NOT NULL,
                sequence INTEGER NOT NULL CHECK(sequence >= 0),
                flow_l_min REAL NOT NULL,
                pressure_kpa REAL NOT NULL,
                consumption_valve_open INTEGER NOT NULL CHECK(consumption_valve_open IN (0, 1)),
                measurements_json TEXT NOT NULL,
                FOREIGN KEY(device_id) REFERENCES devices(device_id)
            );

            CREATE INDEX IF NOT EXISTS idx_telemetry_device_generated
                ON telemetry(device_id, generated_at);
            """
        )


def register_devices(devices):
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as connection:
        for device in devices:
            connection.execute(
                """
                INSERT INTO devices (
                    device_id, name, location, expected_interval_seconds, enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    name = excluded.name,
                    location = excluded.location,
                    expected_interval_seconds = excluded.expected_interval_seconds,
                    enabled = excluded.enabled
                """,
                (
                    device["device_id"], device["name"], device["location"],
                    device["interval_seconds"], int(device.get("enabled", True)), created_at,
                ),
            )


def get_device(device_id):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM devices WHERE device_id = ?", (device_id,)
        ).fetchone()


def save_telemetry(payload: TelemetryIn):
    received_at = datetime.now(timezone.utc).isoformat()
    measurements = payload.measurements
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO telemetry (
                message_id, device_id, generated_at, received_at, sequence,
                flow_l_min, pressure_kpa, consumption_valve_open, measurements_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.message_id, payload.device_id, payload.timestamp.isoformat(), received_at,
                payload.sequence, measurements.flow_l_min, measurements.pressure_kpa,
                int(measurements.consumption_valve_open),
                json.dumps(measurements.model_dump(), ensure_ascii=False),
            ),
        )
        connection.execute(
            "UPDATE devices SET last_seen_at = ? WHERE device_id = ?",
            (received_at, payload.device_id),
        )
        return int(cursor.lastrowid), received_at
