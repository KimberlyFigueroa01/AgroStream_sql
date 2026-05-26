"""
models/lectura.py — Modelo ORM para la tabla 'lecturas'.
Esta es la tabla que demuestra el cuello de botella de SQL.
"""

from sqlalchemy import (
    BigInteger, String, Numeric, Integer, Boolean, func,
    ForeignKey, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from models.base import Base


class Lectura(Base):
    __tablename__ = "lecturas"

    id:        Mapped[int]       = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str]       = mapped_column(String(128), ForeignKey("sensores.id", ondelete="CASCADE"), nullable=False)
    finca_id:  Mapped[str]       = mapped_column(String(64),  ForeignKey("fincas.id",   ondelete="CASCADE"), nullable=False)
    tipo:      Mapped[str]       = mapped_column(String(40), nullable=False)
    valor:     Mapped[float]     = mapped_column(Numeric(10, 4), nullable=False)
    unidad:    Mapped[str]       = mapped_column(String(20), nullable=False)
    fuente:    Mapped[str]       = mapped_column(String(20), nullable=False, default="openmeteo")
    anomalia:  Mapped[bool]      = mapped_column(Boolean, nullable=False, default=False)
    lat:       Mapped[Optional[float]]  = mapped_column(Numeric(9, 6), nullable=True)
    lon:       Mapped[Optional[float]]  = mapped_column(Numeric(9, 6), nullable=True)
    altitud_m: Mapped[Optional[int]]    = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime]  = mapped_column(server_default=func.now())

    # Relaciones
    sensor = relationship("Sensor", back_populates="lecturas")
    finca  = relationship("Finca",  back_populates="lecturas")

    __table_args__ = (
        Index("idx_lecturas_sensor_ts", "sensor_id", timestamp.desc()),
        Index("idx_lecturas_finca_ts",  "finca_id",  timestamp.desc()),
        Index("idx_lecturas_tipo_ts",   "tipo",      timestamp.desc()),
        Index("idx_lecturas_timestamp", timestamp.desc()),
    )

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "sensor_id": self.sensor_id,
            "finca_id":  self.finca_id,
            "tipo":      self.tipo,
            "valor":     float(self.valor),
            "unidad":    self.unidad,
            "fuente":    self.fuente,
            "anomalia":  self.anomalia,
            "lat":       float(self.lat) if self.lat else None,
            "lon":       float(self.lon) if self.lon else None,
            "altitud_m": self.altitud_m,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
