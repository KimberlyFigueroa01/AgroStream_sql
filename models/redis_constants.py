"""
models/redis_constants.py — Constantes para esquema Redis de AgroStream-SQL.
Define patrones de clave, TTLs y tamaños máximos de listas.
"""

# ──────────────────────────────────────────────
# Patrones de clave Redis
# ──────────────────────────────────────────────
SENSOR_ESTADO_PREFIX = "sensor:{}:estado"
"""
Patrón: sensor:{sensor_id}:estado
Tipo: Hash
Propósito: Almacena el estado actual del sensor (última lectura)
"""

FINCA_ULTIMA_PREFIX = "finca:{}:ultima"
"""
Patrón: finca:{finca_id}:ultima
Tipo: Hash
Propósito: Última lectura por tipo de sensor para una finca
Campos: temperatura, humedad, co2, humedad_suelo, radiacion (JSON strings)
"""

SENSOR_STREAM_PREFIX = "sensor:{}:stream"
"""
Patrón: sensor:{sensor_id}:stream
Tipo: List (FIFO)
Propósito: Historial de lecturas del sensor (últimas N)
Elementos: JSON strings de lecturas
"""

ALERTAS_GLOBAL = "alertas:global"
"""
Clave: alertas:global
Tipo: List (FIFO)
Propósito: Cola global de alertas (las más recientes primero)
Elementos: JSON strings de alertas
TTL: Ninguno (las alertas globales se guardan permanentemente)
"""

ALERTAS_FINCA_PREFIX = "alertas:{}"
"""
Patrón: alertas:{finca_id}
Tipo: List (FIFO)
Propósito: Alertas específicas de una finca
Elementos: JSON strings de alertas
TTL: 24 horas
"""

# ──────────────────────────────────────────────
# Tiempos de expiración (TTL)
# ──────────────────────────────────────────────
TTL_24H = 86400
"""Tiempo de vida en segundos: 24 horas (86400 segundos)"""

# ──────────────────────────────────────────────
# Tamaños máximos de listas
# ──────────────────────────────────────────────
HISTORIAL_MAX_LEN = 500
"""Máximo número de lecturas en el historial de un sensor"""

ALERTAS_GLOBAL_MAX_LEN = 1000
"""Máximo número de alertas en la cola global"""

ALERTAS_FINCA_MAX_LEN = 200
"""Máximo número de alertas por finca"""

# ──────────────────────────────────────────────
# Conversión de constantes a valores
# ──────────────────────────────────────────────
def sensor_estado_key(sensor_id: str) -> str:
    """Construye la clave del estado de un sensor."""
    return SENSOR_ESTADO_PREFIX.format(sensor_id)


def finca_ultima_key(finca_id: str) -> str:
    """Construye la clave de la última lectura de una finca."""
    return FINCA_ULTIMA_PREFIX.format(finca_id)


def sensor_stream_key(sensor_id: str) -> str:
    """Construye la clave del stream de un sensor."""
    return SENSOR_STREAM_PREFIX.format(sensor_id)


def alertas_finca_key(finca_id: str) -> str:
    """Construye la clave de alertas de una finca."""
    return ALERTAS_FINCA_PREFIX.format(finca_id)
