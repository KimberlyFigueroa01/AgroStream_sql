"""
models/sensor.py — Modelo ORM para la tabla 'sensores'.
"""

from sqlalchemy import String, Boolean, func, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from models.base import Base


class Sensor(Base):
    __tablename__ = "sensores"

    id:        Mapped[str]      = mapped_column(String(128), primary_key=True)
    finca_id:  Mapped[str]      = mapped_column(String(64), ForeignKey("fincas.id", ondelete="CASCADE"), nullable=False)
    tipo:      Mapped[str]      = mapped_column(String(40), nullable=False)
    unidad:    Mapped[str]      = mapped_column(String(20), nullable=False)
    activo:    Mapped[bool]     = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relaciones
    finca    = relationship("Finca",   back_populates="sensores")
    lecturas = relationship("Lectura", back_populates="sensor", cascade="all, delete-orphan")
    alertas  = relationship("Alerta",  back_populates="sensor", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sensores_finca", "finca_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "finca_id":  self.finca_id,
            "tipo":      self.tipo,
            "unidad":    self.unidad,
            "activo":    self.activo,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
