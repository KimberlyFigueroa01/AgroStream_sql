# models/__init__.py
from models.base import Base, engine, SessionLocal
from models.finca import Finca
from models.sensor import Sensor
from models.lectura import Lectura
from models.alerta import Alerta
from models.metrica_benchmark import MetricaBenchmark

__all__ = [
    "Base", "engine", "SessionLocal",
    "Finca", "Sensor", "Lectura", "Alerta", "MetricaBenchmark",
]
