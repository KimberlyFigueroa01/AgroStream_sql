"""
simulation/simulation_manager.py — Hilo daemon de simulación.
Genera lecturas para todas las fincas en cada ciclo, mide tiempos de INSERT,
y emite eventos WebSocket en tiempo real.
"""

import threading
import time
from datetime import datetime, timezone

import config
from simulation.sensor_virtual import SensorVirtual
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
        self.sensor_virtual = SensorVirtual()
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

        for finca in fincas:
            sensores = self.finca_repo.obtener_sensores(finca["id"])

            # Protección: no generar lecturas si no hay sensores en BD
            if not sensores:
                continue

            for sensor in sensores:
                # Generar lectura simulada
                lectura_data = self.sensor_virtual.generar_lectura(sensor, finca)

                # Ingestar con benchmark medido
                resultado = self.ingesta.ingestar_lectura(lectura_data, finca["nombre"])
                bench = resultado["benchmark"]
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

                # Si hay alerta, emitir
                if resultado["alerta"]:
                    alertas_ciclo.append(resultado["alerta"])

                # Emitir benchmark por cada INSERT
                redis_ref = self.benchmark.obtener_comparacion_redis()
                self.socketio.emit("benchmark_update", {
                    "operacion":        bench["operacion"],
                    "duracion_ms":      bench["duracion_ms"],
                    "filas_tabla":      bench["filas_tabla"],
                    "timestamp":        datetime.now(timezone.utc).isoformat(),
                    "comparacion_redis": redis_ref.get("INSERT_lectura", {}),
                })

            # Medir SELECT de estado actual de la finca (una vez por finca por ciclo)
            try:
                select_result = self.benchmark.medir_select_ultima_finca(finca["id"])
                total_select_ms += select_result["duracion_ms"]
            except Exception:
                pass

        # Emitir alertas del ciclo
        if alertas_ciclo:
            self.socketio.emit("sensor_alerts", alertas_ciclo)

        # Emitir resumen de benchmark del ciclo
        filas = self.benchmark.contar_filas_lecturas()
        avg_insert = total_insert_ms / lecturas_ciclo if lecturas_ciclo > 0 else 0

        self.socketio.emit("simulation_benchmark", {
            "insert_ms":        round(avg_insert, 3),
            "select_ultima_ms": round(total_select_ms / len(fincas) if fincas else 0, 3),
            "filas_lecturas":   filas,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "ciclo":            self._ciclo,
            "lecturas_ciclo":   lecturas_ciclo,
        })
