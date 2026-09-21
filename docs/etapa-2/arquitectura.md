# Arquitectura de backend y persistencia

```text
Cuatro dispositivos simulados
            |
            | JSON mediante HTTP POST
            v
     POST /api/telemetry
            |
            v
 FastAPI y validación Pydantic
            |
            +----> registro de dispositivos
            |
            v
     persistencia SQLite
      devices + telemetry
```

## Recorrido de una lectura

1. Cada dispositivo produce identidad, fecha, secuencia y mediciones.
2. Pydantic valida contrato, tipos y rangos hidráulicos.
3. El endpoint comprueba que el dispositivo esté registrado y habilitado.
4. SQLite impide almacenar dos veces el mismo `message_id`.
5. La lectura se guarda con la hora generada y la hora de recepción.
6. El dispositivo actualiza `last_seen_at`.

## Extensibilidad

Los dispositivos se definen en `simulator/config.json`. Al iniciar, el backend sincroniza el catálogo con la tabla `devices`. Agregar un dispositivo válido no requiere modificar el endpoint. Las reglas hidráulicas son comunes porque los dispositivos representan el mismo tipo de fuente.
