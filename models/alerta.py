"""
models/alerta.py — Modelo ORM para la tabla 'alertas'.
"""

import uuid
from sqlalchemy import (
    String, Numeric, Boolean, Text, func,
    ForeignKey, Index, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from models.base import Base


class Alerta(Base):
    __tablename__ = "alertas"

    id:           Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id:    Mapped[str]       = mapped_column(String(128), ForeignKey("sensores.id", ondelete="CASCADE"), nullable=False)
    finca_id:     Mapped[str]       = mapped_column(String(64),  ForeignKey("fincas.id",   ondelete="CASCADE"), nullable=False)
    finca_nombre: Mapped[str]       = mapped_column(String(120), nullable=False)
    tipo_sensor:  Mapped[str]       = mapped_column(String(40),  nullable=False)
    nivel:        Mapped[str]       = mapped_column(String(20),  nullable=False)
    mensaje:      Mapped[str]       = mapped_column(Text, nullable=False)
    valor:        Mapped[float]     = mapped_column(Numeric(10, 4), nullable=False)
    unidad:       Mapped[str]       = mapped_column(String(20), nullable=False)
    umbral_min:   Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    umbral_max:   Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    timestamp:    Mapped[datetime]  = mapped_column(server_default=func.now())
    leida:        Mapped[bool]      = mapped_column(Boolean, nullable=False, default=False)

    # Relaciones
    sensor = relationship("Sensor", back_populates="alertas")
    finca  = relationship("Finca",  back_populates="alertas")

    __table_args__ = (
        CheckConstraint("nivel IN ('critico','advertencia','info')", name="chk_nivel"),
        Index("idx_alertas_finca_ts",  "finca_id", timestamp.desc()),
        Index("idx_alertas_global_ts", timestamp.desc()),
    )

    def to_dict(self) -> dict:
        return {
            "id":           str(self.id),
            "sensor_id":    self.sensor_id,
            "finca_id":     self.finca_id,
            "finca_nombre": self.finca_nombre,
            "tipo_sensor":  self.tipo_sensor,
            "nivel":        self.nivel,
            "mensaje":      self.mensaje,
            "valor":        float(self.valor),
            "unidad":       self.unidad,
            "umbral_min":   float(self.umbral_min) if self.umbral_min else None,
            "umbral_max":   float(self.umbral_max) if self.umbral_max else None,
            "timestamp":    self.timestamp.isoformat() if self.timestamp else None,
            "leida":        self.leida,
        }
