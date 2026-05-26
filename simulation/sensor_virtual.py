"""
simulation/sensor_virtual.py — Generador de lecturas con ruido gaussiano.
Base Open-Meteo + ruido + deriva lenta + anomalías 0.5%.
Incluye modelo físico local como fallback offline.
"""

import numpy as np
from datetime import datetime
import config
from services.openmeteo_client import OpenMeteoClient


class SensorVirtual:
    """
    Genera lecturas simuladas para un sensor específico.
    Usa datos reales de Open-Meteo como base cuando está disponible,
    con fallback a modelo físico local.
    """

    def __init__(self):
        self.meteo_client = OpenMeteoClient()
        self._deriva = {}  # sensor_id -> drift actual
        self._rng = np.random.default_rng()

    def generar_lectura(self, sensor: dict, finca: dict) -> dict:
        """
        Genera una lectura para un sensor dado, usando condiciones meteorológicas
        reales (o modelo local) como base.

        Args:
            sensor: dict con id, tipo, unidad, finca_id
            finca: dict con id, nombre, lat, lon, altitud_m

        Returns:
            dict con todos los campos necesarios para insertar en lecturas.
        """
        tipo = sensor["tipo"]
        sensor_id = sensor["id"]

        # Obtener condiciones meteorológicas (API o fallback local)
        condiciones = self.meteo_client.obtener_condiciones(
            finca["lat"], finca["lon"], finca.get("altitud_m", 0)
        )
        fuente = condiciones.get("fuente", "openmeteo")

        # Valor base según tipo de sensor
        valor_base = self._valor_base(tipo, condiciones)

        # Ruido gaussiano
        ruido = self._ruido_gaussiano(tipo)

        # Deriva lenta (simula cambios graduales del sensor)
        deriva = self._actualizar_deriva(sensor_id, tipo)

        # Valor final
        valor = valor_base + ruido + deriva

        # Anomalía (0.5% de probabilidad)
        anomalia = False
        if self._rng.random() < 0.005:
            anomalia = True
            # Valor anómalo: fuera de rango normal
            factor = self._rng.choice([-1, 1]) * self._rng.uniform(1.5, 3.0)
            valor = valor + factor * abs(ruido) * 10

        # Clamp a rangos físicamente posibles
        valor = self._clamp_valor(tipo, valor)

        return {
            "sensor_id": sensor_id,
            "finca_id":  finca["id"],
            "tipo":      tipo,
            "valor":     round(valor, 4),
            "unidad":    sensor["unidad"],
            "fuente":    fuente,
            "anomalia":  anomalia,
            "lat":       finca["lat"],
            "lon":       finca["lon"],
            "altitud_m": finca.get("altitud_m"),
        }

    def _valor_base(self, tipo: str, condiciones: dict) -> float:
        """Calcula el valor base según tipo de sensor y condiciones meteorológicas."""
        if tipo == "temperatura":
            return condiciones.get("temperatura", 15.0)
        elif tipo == "humedad":
            return condiciones.get("humedad", 70.0)
        elif tipo == "co2":
            # CO2 ambiental base ~400ppm + variación por vegetación
            base_co2 = 400.0
            hora = datetime.now().hour
            # Más CO2 de noche (respiración), menos de día (fotosíntesis)
            if 6 <= hora <= 18:
                base_co2 -= self._rng.uniform(10, 50)
            else:
                base_co2 += self._rng.uniform(20, 80)
            return base_co2
        elif tipo == "humedad_suelo":
            # Correlaciona con humedad del aire pero con inercia
            humedad_aire = condiciones.get("humedad", 70.0)
            return humedad_aire * 0.6 + self._rng.uniform(-5, 5)
        elif tipo == "radiacion":
            return max(0.0, condiciones.get("radiacion", 200.0))
        return 0.0

    def _ruido_gaussiano(self, tipo: str) -> float:
        """Genera ruido gaussiano según el tipo de sensor."""
        sigma = {
            "temperatura":   0.5,
            "humedad":       2.0,
            "co2":          15.0,
            "humedad_suelo": 1.5,
            "radiacion":    20.0,
        }
        return float(self._rng.normal(0, sigma.get(tipo, 1.0)))

    def _actualizar_deriva(self, sensor_id: str, tipo: str) -> float:
        """
        Simula deriva lenta del sensor (cambios graduales en la calibración).
        Random walk con mean reversion.
        """
        drift_rate = {
            "temperatura":   0.02,
            "humedad":       0.05,
            "co2":           0.5,
            "humedad_suelo": 0.03,
            "radiacion":     0.1,
        }
        rate = drift_rate.get(tipo, 0.01)

        actual = self._deriva.get(sensor_id, 0.0)
        # Mean reversion + random walk
        nuevo = actual * 0.99 + float(self._rng.normal(0, rate))
        self._deriva[sensor_id] = nuevo
        return nuevo

    def _clamp_valor(self, tipo: str, valor: float) -> float:
        """Limita el valor a rangos físicamente posibles."""
        rangos = {
            "temperatura":   (-10.0, 50.0),
            "humedad":       (0.0,   100.0),
            "co2":           (200.0, 2000.0),
            "humedad_suelo": (0.0,   100.0),
            "radiacion":     (0.0,   1500.0),
        }
        rango = rangos.get(tipo, (-999999, 999999))
        return max(rango[0], min(rango[1], valor))
