"""Esquemas externos del backend de telemetría."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


class HydraulicMeasurements(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flow_l_min: float = Field(ge=0.0, le=12.0)
    pressure_kpa: float = Field(ge=100.0, le=250.0)
    consumption_valve_open: StrictBool

    @field_validator("flow_l_min", "pressure_kpa", mode="before")
    @classmethod
    def reject_non_numeric_values(cls, value):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("debe ser un número JSON")
        return value


class TelemetryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")
    device_id: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    timestamp: datetime
    sequence: int = Field(ge=0)
    measurements: HydraulicMeasurements

    @field_validator("sequence", mode="before")
    @classmethod
    def reject_non_integer_sequence(cls, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("sequence debe ser un entero JSON")
        return value

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp debe incluir zona horaria")
        return value

