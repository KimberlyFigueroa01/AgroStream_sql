"""
Lógica de negocio para gestión de fincas.
Inicialización de datos seed (3 fincas con 5 sensores cada una).
"""

import logging
from typing import List, Dict, Any, Optional
from models.base import SessionLocal
from models.finca import Finca
from models.sensor import Sensor

logger = logging.getLogger(__name__)


class FincaService:
    """Servicio de negocio para gestión de fincas."""

    def __init__(self):
        pass

    def inicializar_datos_seed(self):
        """
        Crea las 3 fincas iniciales y sus 5 sensores si no existen.
        Idempotente: verifica si ya hay fincas antes de insertar.
        Se ejecuta al arrancar en app_factory.
        """
        session = SessionLocal()
        try:
            # Verificar si ya hay fincas
            if session.query(Finca).count() > 0:
                logger.info("  ✓ Datos seed ya existentes")
                return

            # Definición de las 3 fincas (solo las que deben existir)
            fincas_data = [
                {
                    "id": "finca_001",
                    "nombre": "Finca La Esperanza",
                    "lat": 5.5236,
                    "lon": -73.1050,
                    "altitud_m": 2600,
                    "ciudad": "Zipaquirá",
                    "departamento": "Cundinamarca",
                    "activa": True,
                },
                {
                    "id": "finca_002",
                    "nombre": "Finca Los Alisos",
                    "lat": 5.7011,
                    "lon": -72.9281,
                    "altitud_m": 2500,
                    "ciudad": "Sogamoso",
                    "departamento": "Boyacá",
                    "activa": True,
                },
                {
                    "id": "finca_003",
                    "nombre": "Finca El Roble",
                    "lat": 5.53,
                    "lon": -73.36,
                    "altitud_m": 2600,
                    "ciudad": "Villa de Leyva",
                    "departamento": "Boyacá",
                    "activa": True,
                },
            ]

            # Definición de los 5 sensores por finca (sin números extra en el ID)
            tipos_sensores = [
                {"tipo": "temperatura", "unidad": "°C"},
                {"tipo": "humedad", "unidad": "%"},
                {"tipo": "co2", "unidad": "ppm"},
                {"tipo": "humedad_suelo", "unidad": "%"},
                {"tipo": "radiacion", "unidad": "W/m²"},
            ]

            # Crear fincas y sus sensores
            for finca_data in fincas_data:
                # Crear finca
                finca = Finca(**finca_data)
                session.add(finca)
                session.flush()  # Asegurar que el ID es válido antes de crear sensores
                logger.info(f"  ✓ Finca creada: {finca.nombre} (id: {finca.id})")

                # Crear sensores para esta finca (5 sensores, un ID único por tipo)
                for sensor_tipo in tipos_sensores:
                    sensor_id = f"{finca.id}:{sensor_tipo['tipo']}"
                    sensor = Sensor(
                        id=sensor_id,
                        finca_id=finca.id,
                        tipo=sensor_tipo["tipo"],
                        unidad=sensor_tipo["unidad"],
                        activo=True,
                    )
                    session.add(sensor)

                logger.info(f"    → {len(tipos_sensores)} sensores creados para {finca.nombre}")

            session.commit()
            logger.info("  ✓ Datos seed completados: 3 fincas × 5 sensores = 15 sensores")

        except Exception as e:
            session.rollback()
            logger.error(f"  ❌ Error al inicializar datos seed: {e}")
            raise
        finally:
            session.close()

    def obtener_todas(self) -> List[Dict[str, Any]]:
        """Retorna todas las fincas activas como diccionarios."""
        session = SessionLocal()
        try:
            fincas = session.query(Finca).filter(Finca.activa == True).all()
            return [
                {
                    "id": f.id,
                    "nombre": f.nombre,
                    "lat": f.lat,
                    "lon": f.lon,
                    "altitud_m": f.altitud_m,
                    "ciudad": f.ciudad,
                    "departamento": f.departamento,
                    "activa": f.activa,
                    "creada_en": f.creada_en.isoformat() if f.creada_en else None,
                    "actualizada_en": f.actualizada_en.isoformat() if f.actualizada_en else None,
                }
                for f in fincas
            ]
        finally:
            session.close()

    def obtener_por_id(self, finca_id: str) -> Optional[Dict[str, Any]]:
        """Retorna una finca por su ID."""
        session = SessionLocal()
        try:
            finca = session.query(Finca).filter(Finca.id == finca_id).first()
            if not finca:
                return None
            return {
                "id": finca.id,
                "nombre": finca.nombre,
                "lat": finca.lat,
                "lon": finca.lon,
                "altitud_m": finca.altitud_m,
                "ciudad": finca.ciudad,
                "departamento": finca.departamento,
                "activa": finca.activa,
                "creada_en": finca.creada_en.isoformat() if finca.creada_en else None,
                "actualizada_en": finca.actualizada_en.isoformat() if finca.actualizada_en else None,
            }
        finally:
            session.close()

    def obtener_sensores(self, finca_id: str) -> List[Dict[str, Any]]:
        """Retorna sensores activos de una finca."""
        session = SessionLocal()
        try:
            sensores = (
                session.query(Sensor)
                .filter(Sensor.finca_id == finca_id, Sensor.activo == True)
                .all()
            )
            return [
                {
                    "id": s.id,
                    "finca_id": s.finca_id,
                    "tipo": s.tipo,
                    "unidad": s.unidad,
                    "activo": s.activo,
                }
                for s in sensores
            ]
        finally:
            session.close()

    # Métodos de compatibilidad con el código existente
    def listar_fincas(self) -> List[Dict[str, Any]]:
        """Retorna todas las fincas activas."""
        return self.obtener_todas()

    def obtener_finca(self, finca_id: str) -> Optional[Dict[str, Any]]:
        """Retorna una finca por ID."""
        return self.obtener_por_id(finca_id)
