"""Simulador hidráulico de telemetría HTTP sin dependencias externas."""

import argparse
import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

SCENARIOS = ("normal", "consumo_anomalo", "fuga")
CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config(path):
    with open(path, encoding="utf-8") as config_file:
        config = json.load(config_file)
    if not config["device_id"] or config["interval_seconds"] <= 0 or config["timeout_seconds"] <= 0:
        raise ValueError("device_id, interval_seconds y timeout_seconds deben ser válidos")
    required = {"flow_l_min", "pressure_kpa", "consumption_valve_open"}
    if not required.issubset(config["variables"]):
        raise ValueError("Faltan variables hidráulicas obligatorias")
    return config


class HydraulicSimulator:
    def __init__(self, config, scenario="normal"):
        if scenario not in SCENARIOS:
            raise ValueError(f"Escenario desconocido: {scenario}")
        self.config = config
        self.scenario = scenario
        self.random = random.Random(config.get("seed"))
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        self.sequence = 0
        self.flow = float(config["variables"]["flow_l_min"]["initial"])
        self.pressure = float(config["variables"]["pressure_kpa"]["initial"])

    def _step(self, name, current, target):
        spec = self.config["variables"][name]
        delta = target - current
        step = min(abs(delta), spec["max_variation"])
        candidate = current + (step if delta > 0 else -step)
        candidate += self.random.uniform(-0.1, 0.1) * spec["max_variation"]
        candidate = max(current - spec["max_variation"], min(current + spec["max_variation"], candidate))
        return round(max(spec["minimum"], min(spec["maximum"], candidate)), spec["decimals"])

    def next_payload(self):
        self.sequence += 1
        # Los valores son ilustrativos para probar software, no límites hidráulicos reales.
        if self.scenario == "normal":
            valve_open = self.sequence % 12 in range(3, 7)
            flow_target, pressure_target = (3.0, 193.0) if valve_open else (0.0, 200.0)
        elif self.scenario == "consumo_anomalo":
            valve_open = True
            flow_target, pressure_target = 5.0, 188.0
        else:
            valve_open = False
            flow_target, pressure_target = 1.2, 195.0
        self.flow = self._step("flow_l_min", self.flow, flow_target)
        self.pressure = self._step("pressure_kpa", self.pressure, pressure_target)
        device_id = self.config["device_id"]
        return {
            "message_id": f"{device_id}-{self.run_id}-{self.sequence:06d}",
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sequence": self.sequence,
            "measurements": {
                "flow_l_min": self.flow,
                "pressure_kpa": self.pressure,
                "consumption_valve_open": valve_open,
            },
        }


def send_payload(url, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description="Simula telemetría hidráulica por HTTP")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--scenario", choices=SCENARIOS, default="normal")
    parser.add_argument("--count", type=int, default=0, help="Número de lecturas; 0 = continuo")
    parser.add_argument("--dry-run", action="store_true", help="Genera JSON sin enviar HTTP")
    args = parser.parse_args()
    if args.count < 0:
        parser.error("--count no puede ser negativo")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_config(args.config)
    simulator = HydraulicSimulator(config, args.scenario)
    sent = 0
    try:
        while args.count == 0 or sent < args.count:
            payload = simulator.next_payload()
            if args.dry_run:
                print(json.dumps(payload, ensure_ascii=False))
            else:
                try:
                    status, response = send_payload(config["http_url"], payload, config["timeout_seconds"])
                    logging.info("%s -> HTTP %s %s", payload["message_id"], status, response)
                except (error.URLError, TimeoutError) as exc:
                    logging.error("%s -> conexión fallida: %s", payload["message_id"], exc)
            sent += 1
            if args.count == 0 or sent < args.count:
                time.sleep(config["interval_seconds"])
    except KeyboardInterrupt:
        logging.info("Simulador detenido")


if __name__ == "__main__":
    main()

