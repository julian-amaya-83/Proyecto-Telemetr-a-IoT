# Monitoreo hidráulico IoT experimental

Proyecto para simular y conservar lecturas de caudal y presión de un sistema hidráulico experimental representativo de una instalación institucional. Su propósito es preparar datos reproducibles para estudiar la identificación de operación normal, consumo anómalo y fugas controladas. No diagnostica la red de la Universidad de San Buenaventura.

## Estado

La Etapa 1 SIM está publicada en la etiqueta `etapa-1-sim-v1.0`. La Etapa 2 añade un backend FastAPI que registra dispositivos, valida telemetría hidráulica y conserva las lecturas en SQLite. MQTT queda para una implementación futura.

## Estructura

- `simulator/config.json`: dispositivos, escenarios, intervalos y variables.
- `simulator/simulator.py`: generación y envío HTTP POST.
- `backend/main.py`: endpoints `/health` y `/api/telemetry`.
- `backend/schemas.py`: contrato y validación con Pydantic.
- `backend/database.py`: registro de dispositivos y persistencia SQLite.
- `database/iot.db`: base generada localmente; no se versiona.
- `tests/`: pruebas del simulador y del backend.
- `docs/decisiones/persistencia.md`: decisiones del modelo de datos.

## Instalación

Se requiere Python 3.10 o superior. Desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

## Probar el simulador sin red

```powershell
python -m simulator.simulator --count 1 --dry-run
```

Cada dispositivo usa el escenario definido en `config.json`. El argumento `--scenario` permite sobrescribir temporalmente el escenario de todos.

## Ejecutar backend y simulador

Terminal 1:

```powershell
python -m uvicorn backend.main:app --reload
```

Compruebe `http://127.0.0.1:8000/health` y `http://127.0.0.1:8000/docs`.

Terminal 2:

```powershell
python -m simulator.simulator --count 5
```

`--count 5` produce cinco mensajes por dispositivo, veinte en total. El backend debe responder HTTP 201 y conservarlos en `database/iot.db`.

## Dispositivos

| Dispositivo | Ubicación | Escenario | Intervalo |
|---|---|---|---:|
| `HYD-001` | Zona A | normal | 5 segundos |
| `HYD-002` | Zona B | consumo anómalo | 10 segundos |
| `HYD-003` | Zona C | fuga | 3 segundos |
| `HYD-004` | Zona D | normal | 7 segundos |

Cada dispositivo mantiene su propia secuencia, estado hidráulico y semilla. Se pueden agregar dispositivos mediante configuración sin modificar el endpoint.

## Ejecutar pruebas

```powershell
python -m pytest tests -q
```

## Validación y respuestas

Cada POST incluye `message_id`, `device_id`, `timestamp`, `sequence` y `measurements`. El backend valida estructura, tipos y rangos; confirma que el dispositivo esté registrado y habilitado; rechaza duplicados; y almacena las variables junto con el JSON validado.

- `201`: lectura validada y almacenada.
- `403`: dispositivo registrado pero deshabilitado.
- `404`: dispositivo no registrado.
- `409`: `message_id` duplicado.
- `422`: contrato, tipo o rango inválido.

## Persistencia

`devices` conserva nombre, ubicación, intervalo esperado, estado y última comunicación. `telemetry` conserva tiempos de generación y recepción, secuencia, caudal, presión, estado de la válvula y JSON de mediciones. Un índice por dispositivo y fecha prepara las consultas históricas.

## Decisiones pendientes

Definir con el piloto los rangos hidráulicos y la regla de alerta. El siguiente incremento agregará consultas de dispositivos, última lectura e históricos. Después se desarrollarán alertas y dashboard.
