#!/usr/bin/env python3
"""
scripts/run_benchmark.py — Ejecutor automático de benchmarks híbridos PostgreSQL + Redis.

Ejecuta la simulación durante un tiempo determinado, recolecta métricas desde la tabla
metricas_benchmark, calcula estadísticas comparativas y genera un informe Markdown.

Uso:
    python scripts/run_benchmark.py --duration 60 --output benchmark_report.md
    python scripts/run_benchmark.py --duration 120 --postgres-only
    python scripts/run_benchmark.py --duration 30 --redis-only
"""

import argparse
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from tabulate import tabulate

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_URL
from models.base import engine, SessionLocal
from models.metrica_benchmark import MetricaBenchmark
from services.benchmark_service import BenchmarkService
from sqlalchemy import func, text


class BenchmarkRunner:
    """Ejecutor de benchmarks con generación de reportes."""
    
    def __init__(self, duration: int, output_file: str, postgres_only: bool = False, redis_only: bool = False):
        self.duration = duration
        self.output_file = output_file
        self.postgres_only = postgres_only
        self.redis_only = redis_only
        self.start_time = None
        self.end_time = None
        self.benchmark_service = BenchmarkService()
        
    def run(self):
        """Ejecuta el benchmark completo."""
        print(f"\n{'='*60}")
        print(f"  🚀 AgroStream Benchmark Runner")
        print(f"{'='*60}\n")
        
        # Validar que Backend está disponible
        print("🔍 Verificando conectividad con PostgreSQL...")
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                print("✓ PostgreSQL conectado\n")
        except Exception as e:
            print(f"❌ Error: No se puede conectar a PostgreSQL")
            print(f"   {e}\n")
            sys.exit(1)
        
        # Registrar timestamp inicial
        self.start_time = datetime.utcnow()
        print(f"⏱️  Recolectando métricas durante {self.duration} segundos...")
        print(f"   Inicio: {self.start_time.isoformat()}Z\n")
        
        # Esperar duración especificada
        time.sleep(self.duration)
        
        self.end_time = datetime.utcnow()
        print(f"\n✓ Período de recolección terminado")
        print(f"   Fin: {self.end_time.isoformat()}Z\n")
        
        # Recolectar estadísticas
        print("📊 Recolectando estadísticas...")
        stats = self._recolectar_estadisticas()
        
        # Generar reporte
        print(f"📝 Generando reporte en {self.output_file}...")
        self._generar_reporte(stats)
        
        print(f"\n✓ ¡Benchmark completado exitosamente!\n")
        print(f"{'='*60}")
        
    def _recolectar_estadisticas(self) -> Dict:
        """Recolecta todas las estadísticas de rendimiento."""
        stats = {
            "periodo": {
                "inicio": self.start_time.isoformat() + "Z",
                "fin": self.end_time.isoformat() + "Z",
                "duracion_s": (self.end_time - self.start_time).total_seconds(),
            },
            "operaciones": {},
            "resumen_volumen": self._resumen_volumen(),
        }
        
        # Obtener todas las operaciones únicas registradas
        operaciones = self._obtener_operaciones_registradas()
        
        print(f"   Operaciones encontradas: {', '.join(operaciones)}")
        
        for operacion in operaciones:
            # Decidir si incluir basado en filtros
            if self.postgres_only and "postgres" not in operacion.lower():
                continue
            if self.redis_only and "postgres" in operacion.lower():
                continue
                
            stats_op = self.benchmark_service.obtener_estadisticas_completas(
                operacion,
                desde_timestamp=self.start_time.isoformat() + "Z"
            )
            
            if stats_op["count"] > 0:
                stats["operaciones"][operacion] = stats_op
        
        return stats
    
    def _obtener_operaciones_registradas(self) -> List[str]:
        """Obtiene la lista de operaciones únicas registradas."""
        with SessionLocal() as session:
            operaciones = session.query(MetricaBenchmark.operacion.distinct()).all()
            return sorted([op[0] for op in operaciones if op[0]])
    
    def _resumen_volumen(self) -> Dict:
        """Calcula resumen de volumen de datos."""
        with engine.connect() as conn:
            # Contar filas en tabla lecturas
            filas_lecturas = conn.execute(text("SELECT COUNT(*) FROM lecturas")).scalar() or 0
            
            # Contar alertas (si existe tabla)
            try:
                filas_alertas = conn.execute(text("SELECT COUNT(*) FROM alertas")).scalar() or 0
            except:
                filas_alertas = 0
            
            # Contar operaciones registradas
            filas_metricas = conn.execute(
                text("SELECT COUNT(*) FROM metricas_benchmark WHERE timestamp >= :desde"),
                {"desde": self.start_time}
            ).scalar() or 0
        
        return {
            "total_lecturas": filas_lecturas,
            "total_alertas": filas_alertas,
            "metricas_registradas": filas_metricas,
        }
    
    def _generar_reporte(self, stats: Dict):
        """Genera el reporte Markdown con estadísticas."""
        lines = []
        
        # Header
        lines.append("# Informe de Benchmark: PostgreSQL vs Redis")
        lines.append("")
        lines.append(f"**Generado**: {datetime.utcnow().isoformat()}Z")
        lines.append(f"**Período**: {stats['periodo']['inicio']} → {stats['periodo']['fin']}")
        lines.append(f"**Duración**: {stats['periodo']['duracion_s']:.1f} segundos")
        lines.append("")
        
        # Resumen de volumen
        lines.append("## 📊 Resumen de Volumen")
        lines.append("")
        lines.append(f"- **Total de lecturas insertadas**: {stats['resumen_volumen']['total_lecturas']:,}")
        lines.append(f"- **Total de alertas generadas**: {stats['resumen_volumen']['total_alertas']:,}")
        lines.append(f"- **Métricas registradas en período**: {stats['resumen_volumen']['metricas_registradas']:,}")
        lines.append("")
        
        # Estadísticas por operación
        if stats['operaciones']:
            lines.append("## 📈 Estadísticas Comparativas")
            lines.append("")
            
            # Separar por tipo
            postgres_ops = {k: v for k, v in stats['operaciones'].items() if 'postgres' in k.lower()}
            redis_ops = {k: v for k, v in stats['operaciones'].items() if 'postgres' not in k.lower()}
            
            # PostgreSQL
            if postgres_ops:
                lines.append("### PostgreSQL Operations")
                lines.append("")
                table_data = self._construir_tabla_estadisticas(postgres_ops)
                lines.append(tabulate(table_data, headers=[
                    "Operación", "Muestras", "Promedio (ms)", "Mediana (ms)",
                    "Mín (ms)", "Máx (ms)", "P95 (ms)", "P99 (ms)"
                ], tablefmt="github"))
                lines.append("")
            
            # Redis
            if redis_ops:
                lines.append("### Redis Operations")
                lines.append("")
                table_data = self._construir_tabla_estadisticas(redis_ops)
                lines.append(tabulate(table_data, headers=[
                    "Operación", "Muestras", "Promedio (ms)", "Mediana (ms)",
                    "Mín (ms)", "Máx (ms)", "P95 (ms)", "P99 (ms)"
                ], tablefmt="github"))
                lines.append("")
            
            # Comparativa PostgreSQL vs Redis
            if postgres_ops and redis_ops:
                lines.append("### 🏆 Comparativa de Rendimiento")
                lines.append("")
                lines.append(self._generar_comparativa(postgres_ops, redis_ops))
                lines.append("")
        
        else:
            lines.append("## ⚠️ Sin datos disponibles")
            lines.append("")
            lines.append("No se encontraron métricas en el período especificado.")
            lines.append("Asegúrate de que el backend está ejecutando la simulación.")
            lines.append("")
        
        # Notas técnicas
        lines.append("## 📝 Notas Técnicas")
        lines.append("")
        lines.append("- **Precisión de mediciones**: time.perf_counter() (microsegundos)")
        lines.append("- **Almacenamiento de métricas**: PostgreSQL tabla `metricas_benchmark`")
        lines.append("- **Backend**: Flask + Socket.IO + SQLAlchemy")
        lines.append("- **Latencia de red**: Incluida en mediciones (backend local)")
        lines.append("")
        
        # Metadata
        lines.append("---")
        lines.append("*Generado por AgroStream Benchmark Runner*")
        
        # Escribir archivo
        content = "\n".join(lines)
        Path(self.output_file).write_text(content, encoding="utf-8")
        
        print(f"   ✓ Reporte guardado: {self.output_file}")
    
    def _construir_tabla_estadisticas(self, operaciones: Dict) -> List[List]:
        """Construye tabla de datos para tabulate."""
        rows = []
        for op_name, stats in operaciones.items():
            rows.append([
                op_name,
                stats['count'],
                f"{stats['avg_ms']:.3f}",
                f"{stats['median_ms']:.3f}",
                f"{stats['min_ms']:.3f}",
                f"{stats['max_ms']:.3f}",
                f"{stats['p95_ms']:.3f}",
                f"{stats['p99_ms']:.3f}",
            ])
        return rows
    
    def _generar_comparativa(self, postgres_ops: Dict, redis_ops: Dict) -> str:
        """Genera texto comparativo entre PostgreSQL y Redis."""
        lines = []
        
        # Calcular promedios agregados
        postgres_avg = sum(s['avg_ms'] for s in postgres_ops.values()) / len(postgres_ops) if postgres_ops else 0
        redis_avg = sum(s['avg_ms'] for s in redis_ops.values()) / len(redis_ops) if redis_ops else 0
        
        if postgres_avg > 0 and redis_avg > 0:
            ratio = postgres_avg / redis_avg
            improvement = ((postgres_avg - redis_avg) / postgres_avg) * 100
            
            lines.append(f"| Métrica | Valor |")
            lines.append(f"|---------|-------|")
            lines.append(f"| Promedio PostgreSQL | {postgres_avg:.3f} ms |")
            lines.append(f"| Promedio Redis | {redis_avg:.3f} ms |")
            lines.append(f"| **Ratio de mejora** | **{ratio:.1f}x más rápido** |")
            lines.append(f"| **Mejora porcentual** | **{improvement:.1f}%** |")
        
        return "\n".join(lines)


def main():
    """Función principal con argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Ejecutor automático de benchmarks híbridos PostgreSQL + Redis para AgroStream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/run_benchmark.py --duration 60
  python scripts/run_benchmark.py --duration 120 --output custom_report.md
  python scripts/run_benchmark.py --duration 30 --postgres-only
  python scripts/run_benchmark.py --duration 30 --redis-only
        """
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Duración de la recolección de métricas en segundos (default: 60)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_report.md",
        help="Ruta del archivo de salida Markdown (default: benchmark_report.md)"
    )
    
    parser.add_argument(
        "--postgres-only",
        action="store_true",
        help="Solo incluir operaciones PostgreSQL"
    )
    
    parser.add_argument(
        "--redis-only",
        action="store_true",
        help="Solo incluir operaciones Redis"
    )
    
    args = parser.parse_args()
    
    # Validar argumentos
    if args.postgres_only and args.redis_only:
        print("❌ Error: No puedes usar --postgres-only y --redis-only simultáneamente")
        sys.exit(1)
    
    # Ejecutar benchmark
    runner = BenchmarkRunner(
        duration=args.duration,
        output_file=args.output,
        postgres_only=args.postgres_only,
        redis_only=args.redis_only
    )
    
    try:
        runner.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  Benchmark cancelado por usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante benchmark: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
