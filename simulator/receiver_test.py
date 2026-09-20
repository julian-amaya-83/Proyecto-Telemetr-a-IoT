"""Receptor HTTP temporal para probar el simulador; no guarda lecturas."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/telemetry":
            self.send_error(404, "Ruta desconocida")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not all(
                key in payload for key in ("message_id", "device_id", "timestamp", "sequence", "measurements")
            ):
                raise ValueError("Faltan campos obligatorios")
        except (ValueError, json.JSONDecodeError):
            self._reply(400, {"error": "JSON o contrato inválido"})
            return
        print(json.dumps(payload, ensure_ascii=False), flush=True)
        self._reply(201, {"status": "received", "message_id": payload["message_id"]})

    def _reply(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("Receptor temporal en http://127.0.0.1:8000/api/telemetry")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()

