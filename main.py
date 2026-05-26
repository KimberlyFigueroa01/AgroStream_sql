"""
main.py — Punto de entrada de AgroStream-SQL.
Crea la aplicación Flask+SocketIO, inicia la simulación como hilo daemon
y arranca el servidor en modo threading (sin eventlet/gevent).
"""

import config
from api.app_factory import create_app

app, socketio = create_app()

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("  AgroStream-SQL  —  Monitoreo Agrícola IoT (PostgreSQL)")
    print(f"  Backend: http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    print(f"  Intervalo de simulación: {config.INTERVALO_LECTURA_S}s")
    print(f"{'='*60}\n")

    socketio.run(
        app,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
