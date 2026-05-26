"""
repositories/alerta_repository.py — Gestión de alertas.
"""

from sqlalchemy import text
from models.base import SessionLocal
from models.alerta import Alerta
from typing import List, Dict, Any


class AlertaRepository:
    """Operaciones de persistencia para alertas de sensores."""

    def crear(self, data: dict) -> dict:
        """Crea una alerta nueva y la retorna como dict."""
        with SessionLocal() as session:
            alerta = Alerta(
                sensor_id=data["sensor_id"],
                finca_id=data["finca_id"],
                finca_nombre=data["finca_nombre"],
                tipo_sensor=data["tipo_sensor"],
                nivel=data["nivel"],
                mensaje=data["mensaje"],
                valor=data["valor"],
                unidad=data["unidad"],
                umbral_min=data.get("umbral_min"),
                umbral_max=data.get("umbral_max"),
            )
            session.add(alerta)
            session.commit()
            session.refresh(alerta)
            return alerta.to_dict()

    def listar_por_finca(self, finca_id: str, limite: int = 50) -> List[Dict[str, Any]]:
        """Retorna las últimas N alertas de una finca."""
        with SessionLocal() as session:
            alertas = (
                session.query(Alerta)
                .filter(Alerta.finca_id == finca_id)
                .order_by(Alerta.timestamp.desc())
                .limit(limite)
                .all()
            )
            return [a.to_dict() for a in alertas]

    def listar_globales(self, limite: int = 100) -> List[Dict[str, Any]]:
        """Retorna las últimas N alertas globales."""
        with SessionLocal() as session:
            alertas = (
                session.query(Alerta)
                .order_by(Alerta.timestamp.desc())
                .limit(limite)
                .all()
            )
            return [a.to_dict() for a in alertas]

    def marcar_leida(self, alerta_id: str) -> bool:
        """Marca una alerta como leída. Retorna True si se encontró."""
        with SessionLocal() as session:
            alerta = session.get(Alerta, alerta_id)
            if alerta:
                alerta.leida = True
                session.commit()
                return True
            return False

    def contar_no_leidas(self) -> int:
        """Retorna el número de alertas no leídas."""
        with SessionLocal() as session:
            return session.query(Alerta).filter(Alerta.leida.is_(False)).count()
