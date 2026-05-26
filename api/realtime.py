"""
api/realtime.py — Eventos Socket.IO.
Registra handlers para conexión/desconexión y eventos del cliente.
Los eventos de servidor (sensor_reading, benchmark_update, etc.)
se emiten desde SimulationManager.
"""

from flask_socketio import SocketIO, emit
from flask import request as flask_request


def register_events(socketio: SocketIO):
    """Registra todos los handlers de eventos WebSocket."""

    @socketio.on("connect")
    def handle_connect():
        sid = flask_request.sid
        print(f"  🔌 Cliente conectado: {sid}")

    @socketio.on("disconnect")
    def handle_disconnect():
        sid = flask_request.sid
        print(f"  ⚡ Cliente desconectado: {sid}")

    @socketio.on("request_farm_data")
    def handle_request_farm_data(data):
        """
        Cliente solicita datos de una finca específica.
        Responde con las últimas lecturas + alertas.
        """
        from repositories.lectura_repository import LecturaRepository
        from services.alert_engine import AlertEngine

        finca_id = data.get("finca_id")
        if not finca_id:
            return

        lectura_repo = LecturaRepository()
        alert_engine = AlertEngine()

        lecturas = lectura_repo.ultimas_por_finca(finca_id)
        alertas = alert_engine.listar_alertas_finca(finca_id, limite=20)

        emit("farm_data", {
            "finca_id": finca_id,
            "lecturas": lecturas,
            "alertas":  alertas,
        })

    @socketio.on("request_sensor_history")
    def handle_request_sensor_history(data):
        """
        Cliente solicita historial de un sensor.
        """
        from repositories.lectura_repository import LecturaRepository

        sensor_id = data.get("sensor_id")
        limite = data.get("limite", 60)
        if not sensor_id:
            return

        lectura_repo = LecturaRepository()
        historial = lectura_repo.historial_sensor(sensor_id, limite)

        emit("sensor_history", {
            "sensor_id": sensor_id,
            "historial": historial,
        })

    @socketio.on("change_interval")
    def handle_change_interval(data):
        """
        Cliente solicita cambiar el intervalo de simulación.
        Usado por el botón "Acelerar simulación".
        """
        from flask import current_app

        nuevo_intervalo = data.get("intervalo", 5)
        sim = current_app.config.get("SIMULATION_MANAGER")
        if sim:
            sim.cambiar_intervalo(nuevo_intervalo)
            socketio.emit("interval_changed", {"intervalo": nuevo_intervalo})
            print(f"  ⏱ Intervalo cambiado a {nuevo_intervalo}s")
