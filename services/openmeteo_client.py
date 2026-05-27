"""
services/openmeteo_client.py — Cliente para Open-Meteo API con caché JSON en disco.
Incluye fallback físico local para operar sin conexión a internet.
"""

import os
import json
import time
import math
import hashlib
from datetime import datetime
from typing import Optional

import requests

import config


class OpenMeteoClient:
    """
    Obtiene datos meteorológicos de Open-Meteo con caché en disco.
    Si la API no responde, usa un modelo físico local como fallback.
    """

    def __init__(self):
        os.makedirs(config.CACHE_DIR_OPENMETEO, exist_ok=True)
        os.makedirs(config.CACHE_DIR_GEOCODING, exist_ok=True)

    def obtener_condiciones(self, lat: float, lon: float, altitud_m: int = 0) -> dict:
        """
        Retorna condiciones meteorológicas actuales.
        Intenta Open-Meteo primero, luego fallback local.
        Retorna: { temperatura, humedad, radiacion, viento, fuente }
        """
        # Intentar caché
        cache_key = self._cache_key(lat, lon)
        cached = self._leer_cache(cache_key, config.CACHE_TTL_OPENMETEO_S)
        if cached:
            cached["fuente"] = "cache"
            return cached

        # Intentar API
        try:
            data = self._consultar_api(lat, lon)
            if data:
                data["fuente"] = "openmeteo"
                self._escribir_cache(cache_key, data)
                return data
        except Exception as e:
            print(f"  ⚠ Open-Meteo no disponible: {e}")

        # Fallback: modelo físico local
        data = self._modelo_fisico_local(lat, lon, altitud_m)
        data["fuente"] = "modelo_local"
        return data

    def obtener_datos(self, lat: float, lon: float, altitud_m: int = 0) -> dict:
        """Alias público para mantener compatibilidad con el resto del sistema."""
        return self.obtener_condiciones(lat, lon, altitud_m)

    # ── Open-Meteo API ───────────────────────────

    def _consultar_api(self, lat: float, lon: float) -> Optional[dict]:
        """Consulta la API de Open-Meteo para condiciones actuales."""
        params = {
            "latitude":  lat,
            "longitude": lon,
            "current":   "temperature_2m,relative_humidity_2m,shortwave_radiation,wind_speed_10m",
            "timezone":  "America/Bogota",
        }
        resp = requests.get(config.OPENMETEO_FORECAST_URL, params=params, timeout=5)
        resp.raise_for_status()
        json_data = resp.json()

        current = json_data.get("current", {})
        return {
            "temperatura": current.get("temperature_2m", 15.0),
            "humedad":     current.get("relative_humidity_2m", 70.0),
            "radiacion":   current.get("shortwave_radiation", 200.0),
            "viento":      current.get("wind_speed_10m", 5.0),
        }

    # ── Modelo físico local (fallback offline) ───

    def _modelo_fisico_local(self, lat: float, lon: float, altitud_m: int = 0) -> dict:
        """
        Genera condiciones meteorológicas basadas en un modelo físico simplificado:
        - Lapse rate altitudinal: -6.5°C por cada 1000m
        - Ciclo diurno: sinusoidal con mínimo a las 5am, máximo a las 2pm
        - Humedad relativa inversamente proporcional a la temperatura
        - Radiación solar basada en hora del día
        """
        now = datetime.now()
        hora = now.hour + now.minute / 60.0

        # ── Temperatura ──
        # Base tropical ajustada por latitud (más al ecuador = más cálido)
        temp_base_nivel_mar = 26.0 - abs(lat - 4.0) * 0.3

        # Lapse rate: -6.5°C / 1000m
        temp_base = temp_base_nivel_mar - (altitud_m * 0.0065)

        # Ciclo diurno: sinusoidal con fase
        # Mínimo ~5am (hora 5), máximo ~2pm (hora 14)
        fase = (hora - 5.0) / 24.0 * 2.0 * math.pi
        amplitud_diurna = 5.0  # ±5°C
        temperatura = temp_base + amplitud_diurna * math.sin(fase)

        # ── Humedad relativa ──
        # Inversamente proporcional a la temperatura, base ~70% para altiplano
        humedad_base = 70.0 + (altitud_m - 2500) * 0.005
        humedad = humedad_base - (temperatura - temp_base) * 2.0
        humedad = max(30.0, min(95.0, humedad))

        # ── Radiación solar ──
        # Solo de día (6am a 6pm), pico a mediodía
        if 6.0 <= hora <= 18.0:
            fase_solar = (hora - 6.0) / 12.0 * math.pi
            radiacion = 800.0 * math.sin(fase_solar)
            radiacion = max(0.0, radiacion)
        else:
            radiacion = 0.0

        # ── Viento ──
        viento = 3.0 + 2.0 * math.sin((hora / 24.0) * 2.0 * math.pi)

        return {
            "temperatura": round(temperatura, 1),
            "humedad":     round(humedad, 1),
            "radiacion":   round(radiacion, 1),
            "viento":      round(viento, 1),
        }

    # ── Caché en disco ───────────────────────────

    def _cache_key(self, lat: float, lon: float) -> str:
        raw = f"{lat:.4f}_{lon:.4f}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _leer_cache(self, key: str, ttl_s: int) -> Optional[dict]:
        path = os.path.join(config.CACHE_DIR_OPENMETEO, f"{key}.json")
        if not os.path.exists(path):
            return None
        mtime = os.path.getmtime(path)
        if time.time() - mtime > ttl_s:
            return None
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _escribir_cache(self, key: str, data: dict):
        path = os.path.join(config.CACHE_DIR_OPENMETEO, f"{key}.json")
        try:
            with open(path, "w") as f:
                json.dump(data, f)
        except IOError:
            pass
