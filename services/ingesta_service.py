"""
services/ingesta_service.py — Validación + persistencia de lecturas + benchmark.
Punto de entrada unificado para la ingesta de datos de sensores.
"""

from services.benchmark_service import BenchmarkService
from services.alert_engine import AlertEngine


class IngestaService:
    """
    Servicio de ingesta que:
    1. Recibe datos de lectura del SimulationManager
    2. Mide el INSERT vía BenchmarkService
    3. Evalúa umbrales vía AlertEngine
    4. Retorna métricas de benchmark + alertas generadas
    """

    def __init__(self):
        self.benchmark = BenchmarkService()
        self.alert_engine = AlertEngine()

    def ingestar_lectura(self, lectura_data: dict, finca_nombre: str) -> dict:
        """
        Ingesta completa de una lectura:
        - INSERT medido (benchmark)
        - Evaluación de alertas
        Retorna: { benchmark: {...}, alerta: {...} | None }
        """
        # 1. INSERT medido por benchmark
        resultado_bench = self.benchmark.medir_insert_lectura(lectura_data)

        # 2. Evaluar alertas
        alerta = self.alert_engine.evaluar(lectura_data, finca_nombre)

        return {
            "benchmark": resultado_bench,
            "alerta":    alerta,
        }

    def obtener_estado_finca(self, finca_id: str) -> dict:
        """
        Obtiene el estado actual de una finca con benchmark medido.
        Retorna: { benchmark: {...}, resultado: [...] }
        """
        return self.benchmark.medir_select_ultima_finca(finca_id)

    def obtener_historial_sensor(self, sensor_id: str, limite: int = 60) -> dict:
        """
        Obtiene el historial de un sensor con benchmark medido.
        Retorna: { benchmark: {...}, resultado: [...] }
        """
        return self.benchmark.medir_select_historial(sensor_id, limite)
