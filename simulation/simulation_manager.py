"""
simulation/simulation_manager.py — Hilo daemon de simulación.
Genera lecturas para todas las fincas en cada ciclo, mide tiempos de INSERT,
y emite eventos WebSocket en tiempo real.
"""

import threading
import time
from datetime import datetime, timezone

import config
from services.openmeteo_client import OpenMeteoClient
from services.ingesta_service import IngestaService
from services.benchmark_service import BenchmarkService
from repositories.finca_repository import FincaRepository


class SimulationManager:
    """
    Hilo daemon que ejecuta ciclos de simulación periódicos.
    Genera lecturas para todas las fincas, mide benchmarks, y emite vía WebSocket.
    """

    def __init__(self, socketio):
        self.socketio = socketio
        self.meteo_client = OpenMeteoClient()
        self.ingesta = IngestaService()
        self.benchmark = BenchmarkService()
        self.finca_repo = FincaRepository()

        self.intervalo = config.INTERVALO_LECTURA_S
        self._running = False
        self._thread = None
        self._ciclo = 0

    def iniciar(self):
        """Arranca el hilo daemon de simulación."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SimulationManager")
        self._thread.start()
        print(f"  🌱 Simulación iniciada (intervalo: {self.intervalo}s)")

    def detener(self):
        """Detiene la simulación."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        print("  🛑 Simulación detenida")

    def cambiar_intervalo(self, nuevo_intervalo: int):
        """Cambia el intervalo de simulación en caliente."""
        self.intervalo = max(1, min(30, nuevo_intervalo))
        print(f"  ⏱ Intervalo actualizado: {self.intervalo}s")

    def _loop(self):
        """Bucle principal de simulación."""
        # Esperar un poco para que Flask arranque completamente
        time.sleep(2)

        while self._running:
            try:
                self._ejecutar_ciclo()
            except Exception as e:
                print(f"  ❌ Error en ciclo de simulación: {e}")
                import traceback
                traceback.print_exc()

            time.sleep(self.intervalo)

    def _ejecutar_ciclo(self):
        """Ejecuta un ciclo completo de simulación para todas las fincas."""
        self._ciclo += 1
        fincas = self.finca_repo.obtener_todas()

        if not fincas:
            return

        total_insert_ms = 0.0
        total_select_ms = 0.0
        lecturas_ciclo = 0
        alertas_ciclo = []
        
        # Acumuladores para métricas Redis
        redis_metrics = {
            "HSET_sensor_estado": [],
            "HSET_finca_ultima": [],
            "LPUSH_historial_sensor": [],
            "LPUSH_alerta_global": [],
            "LPUSH_alerta_finca": [],
        }
        redis_errors = 0

        for finca in fincas:
            sensores = self.finca_repo.obtener_sensores(finca["id"])

            # Protección: no generar lecturas si no hay sensores en BD
            if not sensores:
                continue

            condiciones = self.meteo_client.obtener_datos(
                finca["lat"], finca["lon"], finca.get("altitud_m", 0)
            )
            fuente = condiciones.get("fuente", "openmeteo")
            print(
                f"  \u2601 OpenMeteo {finca['id']} {finca['nombre']} -> "
                f"fuente={fuente}, temp={condiciones.get('temperatura')}, "
                f"hum={condiciones.get('humedad')}, rad={condiciones.get('radiacion')}, "
                f"viento={condiciones.get('viento')}"
            )

            for sensor in sensores:
                valor = self._valor_real(sensor["tipo"], condiciones)
                lectura_data = {
                    "sensor_id": sensor["id"],
                    "finca_id":  finca["id"],
                    "tipo":      sensor["tipo"],
                    "valor":     round(valor, 4),
                    "unidad":    sensor["unidad"],
                    "fuente":    fuente,
                    "anomalia":  False,
                    "lat":       finca["lat"],
                    "lon":       finca["lon"],
                    "altitud_m": finca.get("altitud_m"),
                }
                print(
                    f"  \u2192 Lectura {sensor['id']} tipo={sensor['tipo']} "
                    f"valor={lectura_data['valor']} {lectura_data['unidad']} "
                    f"fuente={lectura_data['fuente']}"
                )

                # Ingestar con benchmark medido (HÍBRIDO: PostgreSQL + Redis)
                resultado = self.ingesta.ingestar_lectura(lectura_data, finca["nombre"])
                bench = resultado["benchmark"]
                redis_status = resultado["redis_status"]
                redis_durations = resultado["redis_durations"]
                
                total_insert_ms += bench["duracion_ms"]
                lecturas_ciclo += 1

                # Emitir lectura vía WebSocket
                self.socketio.emit("sensor_reading", {
                    "finca_id":  finca["id"],
                    "sensor_id": sensor["id"],
                    "tipo":      lectura_data["tipo"],
                    "valor":     lectura_data["valor"],
                    "unidad":    lectura_data["unidad"],
                    "anomalia":  lectura_data["anomalia"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                # Emitir benchmark PostgreSQL
                redis_ref = self.benchmark.obtener_comparacion_redis()
                self.socketio.emit("benchmark_update", {
                    "operacion":        bench["operacion"],
                    "duracion_ms":      bench["duracion_ms"],
                    "filas_tabla":      bench["filas_tabla"],
                    "timestamp":        datetime.now(timezone.utc).isoformat(),
                    "comparacion_redis": redis_ref.get("INSERT_lectura", {}),
                    "db": "postgresql",
                })

                # Emitir benchmarks de Redis (si están disponibles)
                if redis_status == "ok":
                    for op_name, duration in redis_durations.items():
                        if duration is not None and isinstance(duration, (int, float)):
                            # Registrar métrica para acumular
                            if op_name in redis_metrics:
                                redis_metrics[op_name].append(duration)
                            
                            # Emitir evento para cada operación Redis
                            self.socketio.emit("benchmark_update", {
                                "operacion":    op_name,
                                "duracion_ms":  duration,
                                "timestamp":    datetime.now(timezone.utc).isoformat(),
                                "db":           "redis",
                                "finca_id":     finca["id"],
                                "sensor_id":    sensor["id"],
                            })
                elif redis_status == "error":
                    redis_errors += 1

                # Si hay alerta, emitir
                if resultado["alerta"]:
                    alertas_ciclo.append(resultado["alerta"])

            # Medir SELECT de estado actual de la finca (una vez por finca por ciclo)
            try:
                select_result = self.benchmark.medir_select_ultima_finca(finca["id"])
                total_select_ms += select_result["duracion_ms"]
            except Exception:
                pass

        # Emitir alertas del ciclo
        if alertas_ciclo:
            self.socketio.emit("sensor_alerts", alertas_ciclo)

        # Emitir resumen de benchmark del ciclo (incluir métricas Redis)
        filas = self.benchmark.contar_filas_lecturas()
        avg_insert = total_insert_ms / lecturas_ciclo if lecturas_ciclo > 0 else 0
        
        # Calcular promedios de operaciones Redis
        redis_summary = {}
        for op_name, durations in redis_metrics.items():
            if durations:
                redis_summary[op_name] = {
                    "count": len(durations),
                    "promedio_ms": round(sum(durations) / len(durations), 3),
                    "min_ms": round(min(durations), 3),
                    "max_ms": round(max(durations), 3),
                }

        self.socketio.emit("simulation_benchmark", {
            "insert_ms":        round(avg_insert, 3),
            "select_ultima_ms": round(total_select_ms / len(fincas) if fincas else 0, 3),
            "filas_lecturas":   filas,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "ciclo":            self._ciclo,
            "lecturas_ciclo":   lecturas_ciclo,
            "redis_summary":    redis_summary,
            "redis_errors":     redis_errors,
        })

    def _valor_real(self, tipo: str, condiciones: dict) -> float:
        """Mapea condiciones Open-Meteo a los tipos de sensor existentes."""
        if tipo == "temperatura":
            return float(condiciones.get("temperatura", 15.0))
        if tipo == "humedad":
            return float(condiciones.get("humedad", 70.0))
        if tipo == "radiacion":
            return max(0.0, float(condiciones.get("radiacion", 0.0)))
        if tipo == "co2":
            hora = datetime.now().hour
            base = 400.0
            return base - 20.0 if 6 <= hora <= 18 else base + 40.0
        if tipo == "humedad_suelo":
            humedad_aire = float(condiciones.get("humedad", 70.0))
            return max(0.0, min(100.0, humedad_aire * 0.6))
        return 0.0
