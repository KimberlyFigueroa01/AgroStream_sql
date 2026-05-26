"""
models/finca.py — Modelo ORM para la tabla 'fincas'.
"""
from __future__ import annotations

from sqlalchemy import String, Numeric, Integer, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
from models.base import Base


class Finca(Base):
    __tablename__ = "fincas"

    id:             Mapped[str]      = mapped_column(String(64), primary_key=True)
    nombre:         Mapped[str]      = mapped_column(String(120), nullable=False)
    lat:            Mapped[float]    = mapped_column(Numeric(9, 6), nullable=False)
    lon:            Mapped[float]    = mapped_column(Numeric(9, 6), nullable=False)
    altitud_m:      Mapped[int]      = mapped_column(Integer, nullable=False, default=0)
    ciudad:         Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    departamento:   Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    activa:         Mapped[bool]     = mapped_column(Boolean, nullable=False, default=True)
    creada_en:      Mapped[datetime] = mapped_column(server_default=func.now())
    actualizada_en: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Relaciones
    sensores = relationship("Sensor",  back_populates="finca", cascade="all, delete-orphan")
    lecturas = relationship("Lectura", back_populates="finca", cascade="all, delete-orphan")
    alertas  = relationship("Alerta",  back_populates="finca", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "nombre":        self.nombre,
            "lat":           float(self.lat),
            "lon":           float(self.lon),
            "altitud_m":     self.altitud_m,
            "ciudad":        self.ciudad,
            "departamento":  self.departamento,
            "activa":        self.activa,
            "creada_en":     self.creada_en.isoformat() if self.creada_en else None,
            "actualizada_en": self.actualizada_en.isoformat() if self.actualizada_en else None,
        }
