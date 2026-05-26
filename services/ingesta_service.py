"""
services/ingesta_service.py — Validación + persistencia de lecturas + benchmark.
Punto de entrada unificado para la ingesta de datos de sensores.
Soporta escritura híbrida: PostgreSQL (principal) + Redis (caché, medido).
"""

import json
import logging
from typing import Optional, Dict, Any

from services.benchmark_service import BenchmarkService
from services.alert_engine import AlertEngine
from repositories.redis_repository import RedisRepository

# Configurar logging
logger = logging.getLogger(__name__)


class IngestaService:
    """
    Servicio de ingesta que:
    1. Recibe datos de lectura del SimulationManager
    2. Mide el INSERT en PostgreSQL vía BenchmarkService
    3. Mide y guarda copia en Redis (sin romper si falla)
    4. Evalúa umbrales vía AlertEngine
    5. Persiste alertas en PostgreSQL + Redis
    Retorna: { benchmark: {...}, alerta: {...} | None, redis_status: "ok"|"error" }
    """

    def __init__(self, redis_repo: Optional[RedisRepository] = None):
        self.benchmark = BenchmarkService()
        self.alert_engine = AlertEngine()
        self.redis_repo = redis_repo or RedisRepository()

    def ingestar_lectura(self, lectura_data: dict, finca_nombre: str) -> dict:
        """
        Ingesta completa de una lectura con escritura híbrida PostgreSQL + Redis.
        
        Flujo:
        1. INSERT en PostgreSQL (medido, obligatorio)
        2. Guardar copia en Redis (medido, pero no rompe si falla)
        3. Evaluar alertas
        4. Persistir alertas en PostgreSQL + Redis
        
        Returns:
            {
                "benchmark": {...},      # Métricas de PostgreSQL
                "alerta": {...} | None,  # Alerta generada o None
                "redis_status": "ok" | "error",
                "redis_durations": {"HSET_sensor_estado": 1.23, "HSET_finca_ultima": 2.45, ...}
            }
        """
        redis_status = "ok"
        redis_durations = {}
        
        try:
            # 1. INSERT en PostgreSQL (ya medido dentro)
            resultado_bench = self.benchmark.medir_insert_lectura(lectura_data)
            
            # 2. Guardar en Redis (medido, pero no debe romper PostgreSQL si falla)
            try:
                sensor_id = lectura_data["sensor_id"]
                finca_id = lectura_data["finca_id"]
                tipo = lectura_data["tipo"]
                lectura_json = json.dumps(lectura_data)
                
                # 2a. Guardar estado del sensor (HSET)
                _, duracion_hset_estado = self.benchmark.medir(
                    "HSET_sensor_estado",
                    self.redis_repo.guardar_lectura_sensor,
                    sensor_id,
                    lectura_data
                )
                redis_durations["HSET_sensor_estado"] = duracion_hset_estado
                
                # 2b. Actualizar última lectura de la finca (HSET)
                _, duracion_hset_finca = self.benchmark.medir(
                    "HSET_finca_ultima",
                    self.redis_repo.actualizar_ultima_finca,
                    finca_id,
                    tipo,
                    lectura_json
                )
                redis_durations["HSET_finca_ultima"] = duracion_hset_finca
                
                # 2c. Agregar al historial de sensores (LPUSH)
                _, duracion_lpush = self.benchmark.medir(
                    "LPUSH_historial_sensor",
                    self.redis_repo.agregar_historial_sensor,
                    sensor_id,
                    lectura_json
                )
                redis_durations["LPUSH_historial_sensor"] = duracion_lpush
                
            except Exception as e:
                redis_status = "error"
                logger.error(f"❌ Error escribiendo en Redis: {e}. PostgreSQL continuó correctamente.", exc_info=True)
                # No relanzar excepción: PostgreSQL ya funcionó, Redis es opcional
            
            # 3. Evaluar alertas
            alerta = self.alert_engine.evaluar(lectura_data, finca_nombre)
            
            # 4. Persistir alertas en Redis (si hay alerta)
            if alerta:
                try:
                    alerta_json = json.dumps(alerta)
                    finca_id = lectura_data["finca_id"]
                    
                    # 4a. Agregar a alertas globales
                    _, duracion_alerta_global = self.benchmark.medir(
                        "LPUSH_alerta_global",
                        self.redis_repo.agregar_alerta_global,
                        alerta_json
                    )
                    redis_durations["LPUSH_alerta_global"] = duracion_alerta_global
                    
                    # 4b. Agregar a alertas por finca
                    _, duracion_alerta_finca = self.benchmark.medir(
                        "LPUSH_alerta_finca",
                        self.redis_repo.agregar_alerta_finca,
                        finca_id,
                        alerta_json
                    )
                    redis_durations["LPUSH_alerta_finca"] = duracion_alerta_finca
                    
                except Exception as e:
                    logger.error(f"❌ Error guardando alertas en Redis: {e}.", exc_info=True)
                    # Alerta ya está en PostgreSQL gracias a AlertEngine
            
            return {
                "benchmark": resultado_bench,
                "alerta": alerta,
                "redis_status": redis_status,
                "redis_durations": redis_durations,
            }
            
        except Exception as e:
            logger.error(f"❌ Error crítico en ingesta: {e}", exc_info=True)
            raise

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
