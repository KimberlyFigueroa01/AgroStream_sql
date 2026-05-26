"""
models/metrica_benchmark.py — Modelo ORM para la tabla 'metricas_benchmark'.
Corazón de la demo: almacena tiempos de cada operación SQL medida.
"""

from sqlalchemy import BigInteger, String, Numeric, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from models.base import Base


class MetricaBenchmark(Base):
    __tablename__ = "metricas_benchmark"

    id:          Mapped[int]      = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operacion:   Mapped[str]      = mapped_column(String(60), nullable=False)
    duracion_ms: Mapped[float]    = mapped_column(Numeric(10, 3), nullable=False)
    filas_tabla: Mapped[int]      = mapped_column(BigInteger, nullable=False, default=0)
    timestamp:   Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("idx_bench_op", "operacion", timestamp.desc()),
    )

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "operacion":   self.operacion,
            "duracion_ms": float(self.duracion_ms),
            "filas_tabla": self.filas_tabla,
            "timestamp":   self.timestamp.isoformat() if self.timestamp else None,
        }
