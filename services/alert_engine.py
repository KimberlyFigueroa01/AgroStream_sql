"""
services/alert_engine.py — Motor de alertas con umbrales críticos.
Mismos umbrales que AgroStream original: Altiplano Cundiboyacense.
"""

import config
from repositories.alerta_repository import AlertaRepository
from typing import Optional, List, Dict, Any


class AlertEngine:
    """
    Evalúa cada lectura contra los umbrales configurados.
    Genera alertas cuando los valores están fuera de rango.
    """

    def __init__(self):
        self.repo = AlertaRepository()

    def evaluar(self, lectura: dict, finca_nombre: str) -> Optional[Dict[str, Any]]:
        """
        Evalúa una lectura contra los umbrales.
        Si hay violación, crea una alerta y la retorna.
        Retorna None si no hay alerta.
        """
        tipo = lectura["tipo"]
        valor = lectura["valor"]
        umbral = config.UMBRALES.get(tipo)

        if not umbral:
            return None

        umbral_min = umbral.get("min")
        umbral_max = umbral.get("max")

        nivel = None
        mensaje = None

        # Evaluar mínimo
        if umbral_min is not None and valor < umbral_min:
            if tipo == "temperatura" and valor < umbral_min:
                nivel = "critico"
                mensaje = f"⚠️ HELADA: Temperatura de {valor:.1f}°C detectada (umbral: {umbral_min}°C)"
            elif tipo == "humedad_suelo" and valor < umbral_min:
                nivel = "advertencia"
                mensaje = f"Humedad del suelo baja: {valor:.1f}% (umbral: {umbral_min}%)"
            else:
                nivel = "advertencia"
                mensaje = f"{tipo.replace('_', ' ').title()} por debajo del umbral: {valor:.1f} {lectura['unidad']} (mín: {umbral_min})"

        # Evaluar máximo
        if umbral_max is not None and valor > umbral_max:
            if tipo == "temperatura" and valor > umbral_max:
                nivel = "critico"
                mensaje = f"🔥 ESTRÉS TÉRMICO: Temperatura de {valor:.1f}°C (umbral: {umbral_max}°C)"
            elif tipo == "co2" and valor > umbral_max:
                nivel = "critico"
                mensaje = f"CO₂ elevado: {valor:.0f} ppm (umbral: {umbral_max} ppm)"
            elif tipo == "humedad" and valor > umbral_max:
                nivel = "advertencia"
                mensaje = f"Humedad excesiva: {valor:.1f}% (umbral: {umbral_max}%)"
            else:
                nivel = "advertencia"
                mensaje = f"{tipo.replace('_', ' ').title()} por encima del umbral: {valor:.1f} {lectura['unidad']} (máx: {umbral_max})"

        if nivel and mensaje:
            alerta_data = {
                "sensor_id":    lectura["sensor_id"],
                "finca_id":     lectura["finca_id"],
                "finca_nombre": finca_nombre,
                "tipo_sensor":  tipo,
                "nivel":        nivel,
                "mensaje":      mensaje,
                "valor":        valor,
                "unidad":       lectura["unidad"],
                "umbral_min":   umbral_min,
                "umbral_max":   umbral_max,
            }
            return self.repo.crear(alerta_data)

        return None

    def listar_alertas_finca(self, finca_id: str, limite: int = 50) -> List[Dict[str, Any]]:
        """Retorna las últimas alertas de una finca."""
        return self.repo.listar_por_finca(finca_id, limite)

    def listar_alertas_globales(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Retorna las últimas alertas globales."""
        return self.repo.listar_globales(limite)

    def contar_no_leidas(self) -> int:
        """Retorna el número de alertas no leídas."""
        return self.repo.contar_no_leidas()

    def marcar_leida(self, alerta_id: str) -> bool:
        """Marca una alerta como leída."""
        return self.repo.marcar_leida(alerta_id)
