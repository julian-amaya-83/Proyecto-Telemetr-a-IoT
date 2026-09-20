# Propuesta inicial

## Problema y usuario

En un sistema hidráulico experimental, una fuga de baja magnitud puede pasar inadvertida y un consumo prolongado puede confundirse con ella. Una persona que supervisa los ensayos necesita consultar caudal, presión y el estado de la válvula de consumo para decidir qué eventos revisar.

El sistema representa condiciones de uso institucional en un banco experimental. No describe ni diagnostica la red de una sede universitaria.

## Fuente y variables

El dispositivo `HYD-001` es simulado. Produce `flow_l_min` (caudal, L/min), `pressure_kpa` (presión, kPa) y `consumption_valve_open` (estado booleano de la válvula de consumo controlado). Las dos primeras son magnitudes simuladas; la tercera es contexto operativo, no una medición de sensor.

Los rangos y valores de `simulator/config.json` son ilustrativos para probar el software. Deben revisarse con el diseño y piloto del banco hidráulico. La clase experimental normal, consumo anómalo o fuga se elige al ejecutar el simulador y no se envía dentro de `measurements`, para no revelar al futuro detector la respuesta que debe inferir.

## Alerta preliminar

Un posible evento para revisión es caudal persistente mientras la válvula de consumo está cerrada. El umbral de caudal y el número de lecturas consecutivas se definirán después del piloto. Esta regla no demuestra por sí sola que exista una fuga real.

## Arquitectura actual y prevista

Actual: simulador Python → JSON → HTTP POST → receptor temporal de pruebas.

Siguiente incremento: simulador → HTTP POST → FastAPI y validación → SQLite → API de consulta → dashboard. MQTT queda reservado para una implementación futura.

