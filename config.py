"""
config.py — Configuración centralizada de AgroStream-SQL.
Carga variables de entorno desde .env y define constantes del sistema.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent / ".env"
print(">>> Cargando .env desde:", env_path)
load_dotenv(dotenv_path=env_path, override=True)



# ──────────────────────────────────────────────
# Base de datos
# ──────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_KAwvptrW6Q0i@ep-damp-field-aqchkfoj.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require",
)

# ──────────────────────────────────────────────
# Simulación — mismos valores que AgroStream original
# ──────────────────────────────────────────────
INTERVALO_LECTURA_S = int(os.getenv("INTERVALO_LECTURA_S", 5))
PROB_ALERTA_SIMULADA = float(os.getenv("PROB_ALERTA_SIMULADA", 0.03))

SENSORES_POR_FINCA = {
    "temperatura":   2,
    "humedad":       2,
    "co2":           1,
    "humedad_suelo": 3,
    "radiacion":     1,
}

# ──────────────────────────────────────────────
# Umbrales de alerta — Altiplano Cundiboyacense
# ──────────────────────────────────────────────
UMBRALES = {
    "temperatura":   {"min": 2.0,  "max": 35.0},
    "humedad":       {"min": 30.0, "max": 90.0},
    "co2":           {"min": None, "max": 1000.0},
    "humedad_suelo": {"min": 20.0, "max": 80.0},
    "radiacion":     {"min": None, "max": None},
}

# ──────────────────────────────────────────────
# Open-Meteo
# ──────────────────────────────────────────────
OPENMETEO_FORECAST_URL  = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/reverse"
CACHE_DIR_OPENMETEO     = "cache/openmeteo"
CACHE_DIR_GEOCODING     = "cache/geocoding"
CACHE_TTL_OPENMETEO_S   = 3600    # 1 hora
CACHE_TTL_GEOCODING_S   = 86400   # 24 horas

# ──────────────────────────────────────────────
# Flask
# ──────────────────────────────────────────────
FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))  # 5001 para no chocar con AgroStream (5000)
FLASK_HOST = "0.0.0.0"

# ──────────────────────────────────────────────
# Fincas iniciales — mismas que AgroStream
# ──────────────────────────────────────────────
FINCAS = [
    {"id": "finca_001", "nombre": "Finca El Roble",     "lat": 5.5353, "lon": -73.3621, "altitud_m": 2650},
    {"id": "finca_002", "nombre": "Finca La Esperanza", "lat": 4.8833, "lon": -74.0000, "altitud_m": 2600},
    {"id": "finca_003", "nombre": "Finca Los Alisos",   "lat": 5.7011, "lon": -72.9281, "altitud_m": 2500},
]

# ──────────────────────────────────────────────
# Unidades por tipo de sensor
# ──────────────────────────────────────────────
UNIDADES = {
    "temperatura":   "°C",
    "humedad":       "%",
    "co2":           "ppm",
    "humedad_suelo": "%",
    "radiacion":     "W/m²",
}

# ──────────────────────────────────────────────
# Redis Configuration
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
