# Decisiones de persistencia de la Etapa 2

SQLite es suficiente para esta etapa porque permite demostrar validación, integridad, consultas y permanencia después de reiniciar el backend sin administrar otro servidor. Si aumentaran considerablemente los dispositivos, la concurrencia o el volumen de lecturas, sería necesario evaluar PostgreSQL o una base orientada a series temporales.

El modelo utiliza columnas específicas para caudal, presión y estado de la válvula porque son variables estables del dominio y serán consultadas en históricos y gráficas. También conserva `measurements_json` como representación del mensaje validado para facilitar la trazabilidad. Esta solución híbrida evita depender exclusivamente de consultas sobre texto JSON y conserva evidencia del contenido recibido.

Los dispositivos se almacenan en una tabla independiente. El backend registra los dispositivos definidos en la configuración y valida su existencia y estado antes de guardar telemetría. Esto permite incorporar nuevos dispositivos mediante configuración sin modificar el endpoint.
