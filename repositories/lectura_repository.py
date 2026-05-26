"""
repositories/lectura_repository.py — Ingesta y consultas de lecturas.
Usa SQL raw para las queries que se miden en benchmark.
"""

from sqlalchemy import text
from models.base import SessionLocal, engine
from models.lectura import Lectura
from typing import List, Dict, Any


class LecturaRepository:
    """Operaciones de persistencia para lecturas de sensores."""

    def insertar(self, data: dict) -> int:
        """
        Inserta una lectura en la tabla 'lecturas'.
        Retorna el ID generado.
        """
        with SessionLocal() as session:
            lectura = Lectura(
                sensor_id=data["sensor_id"],
                finca_id=data["finca_id"],
                tipo=data["tipo"],
                valor=data["valor"],
                unidad=data["unidad"],
                fuente=data.get("fuente", "openmeteo"),
                anomalia=data.get("anomalia", False),
                lat=data.get("lat"),
                lon=data.get("lon"),
                altitud_m=data.get("altitud_m"),
            )
            session.add(lectura)
            session.commit()
            session.refresh(lectura)
            return lectura.id

    def insertar_raw(self, data: dict) -> int:
        """
        INSERT con SQL raw — usado para medir tiempos sin overhead de ORM.
        Retorna el ID generado.
        """
        sql = text("""
            INSERT INTO lecturas (sensor_id, finca_id, tipo, valor, unidad, fuente, anomalia, lat, lon, altitud_m)
            VALUES (:sensor_id, :finca_id, :tipo, :valor, :unidad, :fuente, :anomalia, :lat, :lon, :altitud_m)
            RETURNING id
        """)
        with engine.connect() as conn:
            result = conn.execute(sql, {
                "sensor_id": data["sensor_id"],
                "finca_id":  data["finca_id"],
                "tipo":      data["tipo"],
                "valor":     data["valor"],
                "unidad":    data["unidad"],
                "fuente":    data.get("fuente", "openmeteo"),
                "anomalia":  data.get("anomalia", False),
                "lat":       data.get("lat"),
                "lon":       data.get("lon"),
                "altitud_m": data.get("altitud_m"),
            })
            conn.commit()
            row = result.fetchone()
            return row[0]

    def ultimas_por_finca_raw(self, finca_id: str) -> List[Dict[str, Any]]:
        """
        SELECT con JOIN — última lectura por tipo para una finca.
        SQL raw para medir tiempos sin ORM.
        """
        sql = text("""
            SELECT DISTINCT ON (l.tipo) l.tipo, l.valor, l.unidad, l.timestamp
            FROM lecturas l
            JOIN sensores s ON s.id = l.sensor_id
            WHERE s.finca_id = :finca_id
            ORDER BY l.tipo, l.timestamp DESC
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"finca_id": finca_id}).fetchall()
            return [
                {
                    "tipo":      row[0],
                    "valor":     float(row[1]),
                    "unidad":    row[2],
                    "timestamp": row[3].isoformat() if row[3] else None,
                }
                for row in rows
            ]

    def historial_sensor_raw(self, sensor_id: str, limite: int = 60) -> List[Dict[str, Any]]:
        """
        SELECT historial de un sensor — SQL raw para benchmark.
        """
        sql = text("""
            SELECT valor, timestamp FROM lecturas
            WHERE sensor_id = :sensor_id
            ORDER BY timestamp DESC LIMIT :limite
        """)
        with engine.connect() as conn:
            rows = conn.execute(sql, {"sensor_id": sensor_id, "limite": limite}).fetchall()
            return [
                {
                    "valor":     float(row[0]),
                    "timestamp": row[1].isoformat() if row[1] else None,
                }
                for row in rows
            ]

    def contar_filas(self) -> int:
        """Retorna el número total de filas en la tabla lecturas."""
        sql = text("SELECT COUNT(*) FROM lecturas")
        with engine.connect() as conn:
            return conn.execute(sql).scalar() or 0

    def ultimas_por_finca(self, finca_id: str) -> List[Dict[str, Any]]:
        """Versión ORM — para uso normal fuera de benchmark."""
        with SessionLocal() as session:
            sql = text("""
                SELECT DISTINCT ON (l.tipo) l.tipo, l.valor, l.unidad, l.timestamp
                FROM lecturas l
                JOIN sensores s ON s.id = l.sensor_id
                WHERE s.finca_id = :finca_id
                ORDER BY l.tipo, l.timestamp DESC
            """)
            rows = session.execute(sql, {"finca_id": finca_id}).fetchall()
            return [
                {
                    "tipo":      row[0],
                    "valor":     float(row[1]),
                    "unidad":    row[2],
                    "timestamp": row[3].isoformat() if row[3] else None,
                }
                for row in rows
            ]

    def historial_sensor(self, sensor_id: str, limite: int = 60) -> List[Dict[str, Any]]:
        """Versión ORM — para uso normal fuera de benchmark."""
        with SessionLocal() as session:
            sql = text("""
                SELECT valor, timestamp FROM lecturas
                WHERE sensor_id = :sensor_id
                ORDER BY timestamp DESC LIMIT :limite
            """)
            rows = session.execute(sql, {"sensor_id": sensor_id, "limite": limite}).fetchall()
            return [
                {
                    "valor":     float(row[0]),
                    "timestamp": row[1].isoformat() if row[1] else None,
                }
                for row in rows
            ]
