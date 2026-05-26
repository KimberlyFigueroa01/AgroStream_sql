"""
api/routes/benchmark.py — Blueprint REST /api/benchmark
Endpoints para el panel de comparación SQL vs Redis.
"""

from flask import Blueprint, jsonify, request
from services.benchmark_service import BenchmarkService

benchmark_bp = Blueprint("benchmark", __name__)

bench_svc = BenchmarkService()


@benchmark_bp.route("/stats", methods=["GET"])
def obtener_stats():
    """
    GET /api/benchmark/stats — Estadísticas agregadas por operación.
    Query param opcional: ?op=INSERT_lectura
    """
    operacion = request.args.get("op")
    if operacion:
        stats = bench_svc.obtener_estadisticas(operacion)
    else:
        stats = bench_svc.obtener_estadisticas_por_operacion()
    return jsonify(stats)


@benchmark_bp.route("/comparacion", methods=["GET"])
def obtener_comparacion():
    """
    GET /api/benchmark/comparacion — Tiempos SQL vs Redis (para el panel).
    Combina las estadísticas reales de SQL con los tiempos de referencia de Redis.
    """
    stats_sql = bench_svc.obtener_estadisticas_por_operacion()
    ref_redis = bench_svc.obtener_comparacion_redis()

    comparacion = {}
    for op, redis_data in ref_redis.items():
        sql_stats = stats_sql.get(op, {})
        comparacion[op] = {
            "sql": {
                "promedio_ms": sql_stats.get("promedio_ms", 0.0),
                "max_ms":      sql_stats.get("max_ms", 0.0),
                "min_ms":      sql_stats.get("min_ms", 0.0),
                "total_ops":   sql_stats.get("total_operaciones", 0),
            },
            "redis": redis_data,
            "filas_actuales": sql_stats.get("filas_actuales", 0),
        }

    return jsonify(comparacion)


@benchmark_bp.route("/historial", methods=["GET"])
def obtener_historial():
    """
    GET /api/benchmark/historial?op=INSERT_lectura&n=100
    Últimas N métricas de una operación.
    """
    operacion = request.args.get("op")
    limite = request.args.get("n", 100, type=int)
    metricas = bench_svc.obtener_historial_metricas(operacion, limite)
    return jsonify(metricas)


@benchmark_bp.route("/reset", methods=["POST"])
def reset_benchmark():
    """
    POST /api/benchmark/reset — Borra metricas_benchmark (NO lecturas).
    Reinicia la demo sin perder el volumen acumulado.
    """
    bench_svc.reset()
    return jsonify({"ok": True, "mensaje": "Métricas de benchmark reiniciadas"})


@benchmark_bp.route("/filas", methods=["GET"])
def obtener_filas():
    """
    GET /api/benchmark/filas — Número actual de filas en tabla lecturas.
    """
    filas = bench_svc.contar_filas_lecturas()
    return jsonify({"filas_lecturas": filas})
