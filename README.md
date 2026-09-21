# Monitoreo hidráulico IoT experimental

Proyecto inicial para simular lecturas de caudal y presión en un sistema hidráulico experimental representativo de una instalación institucional. Su propósito es preparar datos reproducibles para estudiar la identificación de operación normal, consumo anómalo y fugas controladas. No afirma que existan fugas en la Universidad de San Buenaventura.

## Estado

El repositorio contiene un simulador HTTP de cuatro dispositivos, un receptor temporal para pruebas locales y pruebas automatizadas del generador. Cada dispositivo conserva su propia secuencia, estado hidráulico, semilla e intervalo de envío. El backend con validación y SQLite de la Guía 3 es el siguiente incremento. MQTT queda para una implementación futura.

## Estructura

- `simulator/config.json`: dispositivos, URL, intervalos y fichas iniciales de variables.
- `simulator/simulator.py`: escenarios y envío HTTP POST.
- `simulator/receiver_test.py`: receptor temporal que imprime lecturas; no persiste datos.
- `tests/test_simulator.py`: pruebas de contrato, rangos y escenarios.
- `docs/propuesta-inicial.md`: problema, usuario, variables y alerta preliminar.

## Requisitos

Python 3.10 o superior. El simulador y el receptor utilizan únicamente la biblioteca estándar.

## Probar sin red

Desde la raíz del repositorio:

```powershell
python -m simulator.simulator --scenario normal --count 5 --dry-run
python -m simulator.simulator --scenario consumo_anomalo --count 5 --dry-run
python -m simulator.simulator --scenario fuga --count 5 --dry-run
```

## Probar HTTP local

Terminal 1:

```powershell
python -m simulator.receiver_test
```

Terminal 2:

```powershell
python -m simulator.simulator --scenario fuga --count 5
```

`--count 5` genera cinco mensajes por dispositivo, es decir, veinte mensajes en total. El receptor debe imprimirlos y el simulador debe registrar respuestas HTTP 201. Detenga el receptor con Ctrl+C.

## Dispositivos e intervalos

| Dispositivo | Intervalo |
|---|---:|
| `HYD-001` | 5 segundos |
| `HYD-002` | 10 segundos |
| `HYD-003` | 3 segundos |
| `HYD-004` | 7 segundos |

Los cuatro dispositivos comienzan su primera lectura al iniciar el programa. Después, cada uno continúa de acuerdo con su intervalo. Los intervalos pueden modificarse en `simulator/config.json`.

## Ejecutar pruebas

```powershell
python -m unittest discover -s tests -v
```

## Contrato de telemetría

Cada POST a `/api/telemetry` incluye `message_id`, `device_id`, `timestamp` UTC, `sequence` y `measurements`. Cada envío contiene las tres variables habilitadas. `message_id` incorpora el dispositivo, un identificador de ejecución y la secuencia para no repetirse entre dispositivos ni tras reiniciar el simulador.

## Decisiones pendientes

Definir con el piloto los rangos hidráulicos, la variación máxima y la regla de alerta. Añadir validación de tipos y rangos en el backend, persistencia SQLite, API de consultas y dashboard. Registrar integrantes y acuerdos de trabajo cuando el equipo los defina.
