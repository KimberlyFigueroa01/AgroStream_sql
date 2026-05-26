"""
repositories/finca_repository.py — CRUD de fincas con SQLAlchemy.
"""

from models.base import SessionLocal
from models.finca import Finca
from models.sensor import Sensor
from typing import Optional, List, Dict, Any
import config


class FincaRepository:
    """Operaciones de persistencia para fincas y sus sensores."""

    def obtener_todas(self) -> List[Dict[str, Any]]:
        """Retorna todas las fincas activas como dicts."""
        with SessionLocal() as session:
            fincas = session.query(Finca).filter(Finca.activa.is_(True)).all()
            return [f.to_dict() for f in fincas]

    def obtener_por_id(self, finca_id: str) -> Optional[Dict[str, Any]]:
        """Retorna una finca por su ID, o None si no existe."""
        with SessionLocal() as session:
            finca = session.get(Finca, finca_id)
            return finca.to_dict() if finca else None

    def crear_finca(self, data: dict) -> dict:
        """Crea una finca nueva en la BD."""
        with SessionLocal() as session:
            finca = Finca(
                id=data["id"],
                nombre=data["nombre"],
                lat=data["lat"],
                lon=data["lon"],
                altitud_m=data.get("altitud_m", 0),
                ciudad=data.get("ciudad"),
                departamento=data.get("departamento"),
            )
            session.add(finca)
            session.commit()
            session.refresh(finca)
            return finca.to_dict()

    def existe(self, finca_id: str) -> bool:
        """Verifica si una finca existe en la BD."""
        with SessionLocal() as session:
            return session.get(Finca, finca_id) is not None

    def obtener_sensores(self, finca_id: str) -> List[Dict[str, Any]]:
        """Retorna todos los sensores activos de una finca."""
        with SessionLocal() as session:
            sensores = (
                session.query(Sensor)
                .filter(Sensor.finca_id == finca_id, Sensor.activo.is_(True))
                .all()
            )
            return [s.to_dict() for s in sensores]

    def crear_sensores_iniciales(self, finca_id: str) -> List[Dict[str, Any]]:
        """
        Crea los 9 sensores por finca según SENSORES_POR_FINCA del config.
        Retorna la lista de sensores creados.
        """
        creados = []
        with SessionLocal() as session:
            for tipo, cantidad in config.SENSORES_POR_FINCA.items():
                unidad = config.UNIDADES[tipo]
                for i in range(1, cantidad + 1):
                    sensor_id = f"{finca_id}:{tipo}:{i}"
                    # Solo crear si no existe
                    if not session.get(Sensor, sensor_id):
                        sensor = Sensor(
                            id=sensor_id,
                            finca_id=finca_id,
                            tipo=tipo,
                            unidad=unidad,
                        )
                        session.add(sensor)
                        creados.append(sensor_id)
            session.commit()
        return creados
