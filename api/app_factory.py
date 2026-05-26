"""
api/app_factory.py — Composition root.
Crea la aplicación Flask + SocketIO, registra blueprints,
configura CORS, inicializa BD + datos seed, y arranca la simulación.
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

import config
from models.base import Base, engine

# SocketIO global — accesible desde otros módulos
socketio = SocketIO()


def create_app() -> tuple:
    """
    Crea y configura la aplicación Flask con SocketIO.
    Retorna: (app, socketio)
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "agrostream-sql-demo-2024"

    # ── CORS ──
    # Configurado directamente aquí, no en middleware separado
    CORS(app, origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
    ])

    # ── SocketIO ──
    # async_mode='threading' — sin eventlet ni gevent
    socketio.init_app(app, cors_allowed_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
    ], async_mode="threading")

    # ── Registrar Blueprints ──
    from api.routes.fincas import fincas_bp
    from api.routes.benchmark import benchmark_bp
    app.register_blueprint(fincas_bp, url_prefix="/api/fincas")
    app.register_blueprint(benchmark_bp, url_prefix="/api/benchmark")

    # ── Registrar eventos SocketIO ──
    from api.realtime import register_events
    register_events(socketio)

    # ── Inicializar BD ──
    with app.app_context():
        _init_database()

    # ── Arrancar simulación ──
    # Importar aquí para evitar circular imports
    from simulation.simulation_manager import SimulationManager
    sim = SimulationManager(socketio)
    sim.iniciar()

    # Guardar referencia al sim en app para control desde API
    app.config["SIMULATION_MANAGER"] = sim

    return app, socketio


def _init_database():
    """
    Crea las tablas si no existen y ejecuta el seed de datos iniciales.
    El seed SIEMPRE se ejecuta antes de que arranque la simulación.
    """
    print("\n── Inicializando base de datos ──")

    # Asegurarse de que SQLAlchemy vea todos los modelos antes de crear tablas.
    import models
    print("  engine.url =", engine.url)
    print(
        "  model imports:",
        [models.Finca.__name__, models.Sensor.__name__, models.Lectura.__name__, models.Alerta.__name__, models.MetricaBenchmark.__name__],
    )

    # Crear todas las tablas definidas en los modelos
    Base.metadata.create_all(bind=engine)
    print("  ✓ Tablas creadas/verificadas")

    from sqlalchemy import inspect
    inspector = inspect(engine)
    tablas = inspector.get_table_names()
    print("  Tablas encontradas en BD:", tablas)

    # Seed: fincas + sensores
    from services.finca_service import FincaService
    finca_svc = FincaService()
    finca_svc.inicializar_datos_seed()

    print("  ✓ Datos seed listos\n")
