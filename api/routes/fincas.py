"""
api/routes/fincas.py — Blueprint REST /api/fincas
Endpoints para gestión de fincas, lecturas y alertas.
"""

from flask import Blueprint, jsonify, request
from services.finca_service import FincaService
from repositories.lectura_repository import LecturaRepository
from services.alert_engine import AlertEngine

fincas_bp = Blueprint("fincas", __name__)

finca_svc = FincaService()
lectura_repo = LecturaRepository()
alert_engine = AlertEngine()


@fincas_bp.route("/", methods=["GET"])
def listar_fincas():
    """GET /api/fincas/ — Lista todas las fincas activas."""
    fincas = finca_svc.listar_fincas()
    return jsonify(fincas)


@fincas_bp.route("/<finca_id>", methods=["GET"])
def obtener_finca(finca_id: str):
    """GET /api/fincas/<id> — Detalle de una finca."""
    finca = finca_svc.obtener_finca(finca_id)
    if not finca:
        return jsonify({"error": "Finca no encontrada"}), 404
    return jsonify(finca)


@fincas_bp.route("/<finca_id>/sensores", methods=["GET"])
def obtener_sensores(finca_id: str):
    """GET /api/fincas/<id>/sensores — Sensores de una finca."""
    sensores = finca_svc.obtener_sensores(finca_id)
    return jsonify(sensores)


@fincas_bp.route("/<finca_id>/lecturas", methods=["GET"])
def obtener_lecturas(finca_id: str):
    """GET /api/fincas/<id>/lecturas — Últimas lecturas por tipo de una finca."""
    lecturas = lectura_repo.ultimas_por_finca(finca_id)
    return jsonify(lecturas)


@fincas_bp.route("/<finca_id>/historial/<sensor_id>", methods=["GET"])
def obtener_historial(finca_id: str, sensor_id: str):
    """GET /api/fincas/<id>/historial/<sensor_id> — Historial de un sensor."""
    limite = request.args.get("limite", 60, type=int)
    # sensor_id viene URL-encoded, reconstruir con finca_id
    full_sensor_id = f"{finca_id}:{sensor_id}" if ":" not in sensor_id else sensor_id
    historial = lectura_repo.historial_sensor(full_sensor_id, limite)
    return jsonify(historial)


@fincas_bp.route("/<finca_id>/alertas", methods=["GET"])
def obtener_alertas(finca_id: str):
    """GET /api/fincas/<id>/alertas — Alertas de una finca."""
    limite = request.args.get("limite", 50, type=int)
    alertas = alert_engine.listar_alertas_finca(finca_id, limite)
    return jsonify(alertas)


@fincas_bp.route("/alertas/globales", methods=["GET"])
def obtener_alertas_globales():
    """GET /api/fincas/alertas/globales — Todas las alertas recientes."""
    limite = request.args.get("limite", 100, type=int)
    alertas = alert_engine.listar_alertas_globales(limite)
    return jsonify(alertas)


@fincas_bp.route("/alertas/no-leidas", methods=["GET"])
def contar_alertas_no_leidas():
    """GET /api/fincas/alertas/no-leidas — Conteo de alertas no leídas."""
    count = alert_engine.contar_no_leidas()
    return jsonify({"no_leidas": count})


@fincas_bp.route("/alertas/<alerta_id>/leer", methods=["POST"])
def marcar_alerta_leida(alerta_id: str):
    """POST /api/fincas/alertas/<id>/leer — Marcar alerta como leída."""
    ok = alert_engine.marcar_leida(alerta_id)
    if not ok:
        return jsonify({"error": "Alerta no encontrada"}), 404
    return jsonify({"ok": True})
