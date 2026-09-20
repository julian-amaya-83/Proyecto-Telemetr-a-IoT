import unittest
import threading
from pathlib import Path
from http.server import HTTPServer

from simulator.receiver_test import Handler
from simulator.simulator import HydraulicSimulator, load_config, send_payload


CONFIG = Path(__file__).resolve().parents[1] / "simulator" / "config.json"


class SimulatorTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(CONFIG)

    def test_contract_and_gradual_changes(self):
        simulator = HydraulicSimulator(self.config, "normal")
        previous = {"flow_l_min": 0.0, "pressure_kpa": 200.0}
        ids = set()
        for sequence in range(1, 30):
            payload = simulator.next_payload()
            self.assertEqual(payload["sequence"], sequence)
            self.assertEqual(payload["device_id"], "HYD-001")
            self.assertTrue(payload["timestamp"].endswith("Z"))
            self.assertNotIn(payload["message_id"], ids)
            ids.add(payload["message_id"])
            values = payload["measurements"]
            self.assertIsInstance(values["consumption_valve_open"], bool)
            for name in previous:
                spec = self.config["variables"][name]
                self.assertGreaterEqual(values[name], spec["minimum"])
                self.assertLessEqual(values[name], spec["maximum"])
                self.assertLessEqual(abs(values[name] - previous[name]), spec["max_variation"] + 0.001)
                previous[name] = values[name]

    def test_leak_has_flow_with_consumption_valve_closed(self):
        simulator = HydraulicSimulator(self.config, "fuga")
        readings = [simulator.next_payload()["measurements"] for _ in range(6)]
        self.assertTrue(all(not r["consumption_valve_open"] for r in readings))
        self.assertGreater(readings[-1]["flow_l_min"], 0.2)

    def test_anomalous_consumption_keeps_valve_open(self):
        simulator = HydraulicSimulator(self.config, "consumo_anomalo")
        readings = [simulator.next_payload()["measurements"] for _ in range(6)]
        self.assertTrue(all(r["consumption_valve_open"] for r in readings))
        self.assertGreater(readings[-1]["flow_l_min"], 3.0)

    def test_http_post_to_local_receiver(self):
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        try:
            payload = HydraulicSimulator(self.config).next_payload()
            status, response = send_payload(
                f"http://127.0.0.1:{server.server_port}/api/telemetry", payload, 2
            )
            self.assertEqual(status, 201)
            self.assertIn(payload["message_id"], response)
        finally:
            thread.join(timeout=3)
            server.server_close()


if __name__ == "__main__":
    unittest.main()

