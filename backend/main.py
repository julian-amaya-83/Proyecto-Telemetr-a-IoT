"""API de ingreso y persistencia de telemetría hidráulica."""

from contextlib import asynccontextmanager
from sqlite3 import IntegrityError

from fastapi import FastAPI, HTTPException, status

from backend.config import load_project_config
from backend.database import get_device, init_db, register_devices, save_telemetry
from backend.schemas import TelemetryIn


@asynccontextmanager
async def lifespan(app):
    config = load_project_config()
    init_db()
    register_devices(config["devices"])
    yield


app = FastAPI(
    title="Backend de Telemetría Hidráulica IoT",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/telemetry", status_code=status.HTTP_201_CREATED)
def receive_telemetry(payload: TelemetryIn):
    device = get_device(payload.device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositivo no registrado")
    if not device["enabled"]:
        raise HTTPException(status_code=403, detail="Dispositivo deshabilitado")
    try:
        row_id, received_at = save_telemetry(payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="message_id duplicado") from exc
    return {
        "status": "accepted",
        "id": row_id,
        "message_id": payload.message_id,
        "device_id": payload.device_id,
        "received_at": received_at,
    }

