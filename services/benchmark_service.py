"""
services/benchmark_service.py — Componente central de la demo.
Mide el tiempo real de cada operación SQL y lo guarda en metricas_benchmark.
Usa time.perf_counter() para máxima precisión en milisegundos.
"""

import time
from sqlalchemy import text
from models.base import engine, SessionLocal
from models.metrica_benchmark import MetricaBenchmark
from typing import List, Dict, Any, Optional


class BenchmarkService:
    """
    Mide el tiempo real de cada operación SQL y lo guarda en metricas_benchmark.
    El frontend lee estas métricas por WebSocket para mostrarlas en tiempo real.
    """

    def medir_insert_lectura(self, lectura_data: dict) -> dict:
        """
        Mide el tiempo de INSERT en lecturas (incluyendo actualización de índices).
        Retorna: { duracion_ms, filas_tabla, operacion, lectura_id }
        """
        sql_insert = text("""
            INSERT INTO lecturas (sensor_id, finca_id, tipo, valor, unidad, fuente, anomalia, lat, lon, altitud_m)
            VALUES (:sensor_id, :finca_id, :tipo, :valor, :unidad, :fuente, :anomalia, :lat, :lon, :altitud_m)
            RETURNING id
        """)
        sql_count = text("SELECT COUNT(*) FROM lecturas")

        with engine.connect() as conn:
            # Medir INSERT
            t0 = time.perf_counter()
            result = conn.execute(sql_insert, {
                "sensor_id": lectura_data["sensor_id"],
                "finca_id":  lectura_data["finca_id"],
                "tipo":      lectura_data["tipo"],
                "valor":     lectura_data["valor"],
                "unidad":    lectura_data["unidad"],
                "fuente":    lectura_data.get("fuente", "openmeteo"),
                "anomalia":  lectura_data.get("anomalia", False),
                "lat":       lectura_data.get("lat"),
                "lon":       lectura_data.get("lon"),
                "altitud_m": lectura_data.get("altitud_m"),
            })
            conn.commit()
            t1 = time.perf_counter()

            lectura_id = result.fetchone()[0]
            duracion_ms = (t1 - t0) * 1000.0

            # Contar filas actuales
            filas = conn.execute(sql_count).scalar() or 0

        # Registrar métrica
        self._registrar_metrica("INSERT_lectura", duracion_ms, filas)

        return {
            "operacion":   "INSERT_lectura",
            "duracion_ms": round(duracion_ms, 3),
            "filas_tabla": filas,
            "lectura_id":  lectura_id,
        }

    def medir_select_ultima_finca(self, finca_id: str) -> dict:
        """
        Mide el tiempo del SELECT con JOIN para obtener última lectura por finca.
        Retorna: { duracion_ms, filas_tabla, operacion, resultado }
        """
        sql_select = text("""
            SELECT DISTINCT ON (l.tipo) l.tipo, l.valor, l.unidad, l.timestamp
            FROM lecturas l
            JOIN sensores s ON s.id = l.sensor_id
            WHERE s.finca_id = :finca_id
            ORDER BY l.tipo, l.timestamp DESC
        """)
        sql_count = text("SELECT COUNT(*) FROM lecturas")

        with engine.connect() as conn:
            t0 = time.perf_counter()
            rows = conn.execute(sql_select, {"finca_id": finca_id}).fetchall()
            t1 = time.perf_counter()

            duracion_ms = (t1 - t0) * 1000.0
            filas = conn.execute(sql_count).scalar() or 0

        resultado = [
            {
                "tipo":      row[0],
                "valor":     float(row[1]),
                "unidad":    row[2],
                "timestamp": row[3].isoformat() if row[3] else None,
            }
            for row in rows
        ]

        self._registrar_metrica("SELECT_ultima_finca", duracion_ms, filas)

        return {
            "operacion":   "SELECT_ultima_finca",
            "duracion_ms": round(duracion_ms, 3),
            "filas_tabla": filas,
            "resultado":   resultado,
        }

    def medir_select_historial(self, sensor_id: str, limite: int = 60) -> dict:
        """
        Mide el tiempo de SELECT para el historial de un sensor.
        Retorna: { duracion_ms, filas_tabla, operacion, resultado }
        """
        sql_select = text("""
            SELECT valor, timestamp FROM lecturas
            WHERE sensor_id = :sensor_id
            ORDER BY timestamp DESC LIMIT :limite
        """)
        sql_count = text("SELECT COUNT(*) FROM lecturas")

        with engine.connect() as conn:
            t0 = time.perf_counter()
            rows = conn.execute(sql_select, {"sensor_id": sensor_id, "limite": limite}).fetchall()
            t1 = time.perf_counter()

            duracion_ms = (t1 - t0) * 1000.0
            filas = conn.execute(sql_count).scalar() or 0

        resultado = [
            {
                "valor":     float(row[0]),
                "timestamp": row[1].isoformat() if row[1] else None,
            }
            for row in rows
        ]

        self._registrar_metrica("SELECT_historial", duracion_ms, filas)

        return {
            "operacion":   "SELECT_historial",
            "duracion_ms": round(duracion_ms, 3),
            "filas_tabla": filas,
            "resultado":   resultado,
        }

    def obtener_estadisticas(self, operacion: str = None, ultimas_n: int = 100) -> dict:
        """
        Retorna estadísticas agregadas de las métricas registradas.
        { promedio_ms, mediana_ms, max_ms, min_ms, total_operaciones, filas_actuales }
        """
        with SessionLocal() as session:
            if operacion:
                metricas = (
                    session.query(MetricaBenchmark)
                    .filter(MetricaBenchmark.operacion == operacion)
                    .order_by(MetricaBenchmark.timestamp.desc())
                    .limit(ultimas_n)
                    .all()
                )
            else:
                metricas = (
                    session.query(MetricaBenchmark)
                    .order_by(MetricaBenchmark.timestamp.desc())
                    .limit(ultimas_n)
                    .all()
                )

        if not metricas:
            return {
                "promedio_ms": 0.0,
                "mediana_ms":  0.0,
                "max_ms":      0.0,
                "min_ms":      0.0,
                "total_operaciones": 0,
                "filas_actuales":    0,
            }

        duraciones = sorted([float(m.duracion_ms) for m in metricas])
        n = len(duraciones)
        mediana = duraciones[n // 2] if n % 2 == 1 else (duraciones[n // 2 - 1] + duraciones[n // 2]) / 2

        return {
            "promedio_ms": round(sum(duraciones) / n, 3),
            "mediana_ms":  round(mediana, 3),
            "max_ms":      round(max(duraciones), 3),
            "min_ms":      round(min(duraciones), 3),
            "total_operaciones": n,
            "filas_actuales":    metricas[0].filas_tabla if metricas else 0,
        }

    def obtener_estadisticas_por_operacion(self, ultimas_n: int = 100) -> dict:
        """Retorna estadísticas agrupadas por tipo de operación."""
        ops = ["INSERT_lectura", "SELECT_ultima_finca", "SELECT_historial"]
        resultado = {}
        for op in ops:
            resultado[op] = self.obtener_estadisticas(op, ultimas_n)
        return resultado

    def obtener_historial_metricas(self, operacion: str = None, limite: int = 100) -> List[Dict[str, Any]]:
        """Retorna las últimas N métricas como lista de dicts."""
        with SessionLocal() as session:
            query = session.query(MetricaBenchmark)
            if operacion:
                query = query.filter(MetricaBenchmark.operacion == operacion)
            metricas = query.order_by(MetricaBenchmark.timestamp.desc()).limit(limite).all()
            return [m.to_dict() for m in metricas]

    def obtener_comparacion_redis(self) -> dict:
        """
        Retorna un dict con los tiempos típicos de Redis para las mismas operaciones,
        tomados de la documentación oficial (constantes, no medidas reales).
        """
        return {
            "INSERT_lectura":      {"referencia_ms": 0.5, "descripcion": "HSET + LPUSH + LTRIM"},
            "SELECT_ultima_finca": {"referencia_ms": 0.3, "descripcion": "HGETALL finca:{id}:ultima"},
            "SELECT_historial":    {"referencia_ms": 0.4, "descripcion": "LRANGE sensor:{id}:stream 0 59"},
        }

    def reset(self):
        """Borra la tabla metricas_benchmark (NO lecturas)."""
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM metricas_benchmark"))
            conn.commit()

    def contar_filas_lecturas(self) -> int:
        """Retorna el número actual de filas en tabla lecturas."""
        with engine.connect() as conn:
            return conn.execute(text("SELECT COUNT(*) FROM lecturas")).scalar() or 0

    # ── Internos ─────────────────────────────────

    def _registrar_metrica(self, operacion: str, duracion_ms: float, filas_tabla: int):
        """Inserta un registro en metricas_benchmark."""
        with SessionLocal() as session:
            metrica = MetricaBenchmark(
                operacion=operacion,
                duracion_ms=round(duracion_ms, 3),
                filas_tabla=filas_tabla,
            )
            session.add(metrica)
            session.commit()
