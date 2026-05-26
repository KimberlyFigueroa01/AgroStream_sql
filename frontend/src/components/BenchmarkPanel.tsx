/**
 * BenchmarkPanel.tsx — Panel central de la demo: comparación SQL vs Redis.
 *
 * Secciones:
 * 1. Comparación en tiempo real (barras comparativas)
 * 2. Gráfica de tendencia de latencia
 * 3. Estadísticas acumuladas
 * 4. Explicación contextual dinámica
 */

import React, { useEffect, useState, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import {
  Database,
  Zap,
  TrendingUp,
  BarChart3,
  RotateCcw,
  Info,
  Gauge,
} from "lucide-react";
import { getSocket } from "../lib/socket";
import {
  getBenchmarkComparacion,
  getBenchmarkHistorial,
  resetBenchmark,
  getFilasLecturas,
} from "../lib/api";
import type {
  BenchmarkComparison,
  BenchmarkMetric,
  SimulationBenchmarkEvent,
} from "../lib/types";

const OP_LABELS: Record<string, string> = {
  INSERT_lectura: "INSERT lectura",
  SELECT_ultima_finca: "Leer estado finca",
  SELECT_historial: "Historial sensor",
};

const OP_DESCRIPTIONS: Record<string, { sql: string; redis: string }> = {
  INSERT_lectura: {
    sql: "INSERT + 4 índices B-tree",
    redis: "HSET + LPUSH + LTRIM",
  },
  SELECT_ultima_finca: {
    sql: "SELECT + JOIN 2 tablas",
    redis: "HGETALL finca:{id}:ultima",
  },
  SELECT_historial: {
    sql: "SELECT + ORDER BY + LIMIT",
    redis: "LRANGE sensor:{id}:stream 0 59",
  },
};

export default function BenchmarkPanel() {
  const [comparacion, setComparacion] = useState<Record<string, BenchmarkComparison>>({});
  const [historial, setHistorial] = useState<BenchmarkMetric[]>([]);
  const [latestBench, setLatestBench] = useState<SimulationBenchmarkEvent | null>(null);
  const [filas, setFilas] = useState(0);
  const [isResetting, setIsResetting] = useState(false);

  // Trend data para la gráfica
  const [trendData, setTrendData] = useState<
    { filas: number; insert_ms: number; select_ms: number }[]
  >([]);

  // Cargar datos iniciales
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [comp, hist, filasRes] = await Promise.all([
        getBenchmarkComparacion(),
        getBenchmarkHistorial("INSERT_lectura", 200),
        getFilasLecturas(),
      ]);
      setComparacion(comp);
      setHistorial(hist);
      setFilas(filasRes.filas_lecturas);
    } catch (err) {
      console.error("Error cargando benchmark:", err);
    }
  }

  // WebSocket: benchmark en tiempo real
  useEffect(() => {
    const socket = getSocket();

    const handleSimBench = (data: SimulationBenchmarkEvent) => {
      setLatestBench(data);
      setFilas(data.filas_lecturas);

      setTrendData((prev) => {
        const next = [
          ...prev,
          {
            filas: data.filas_lecturas,
            insert_ms: data.insert_ms,
            select_ms: data.select_ultima_ms,
          },
        ];
        return next.slice(-200);
      });
    };

    const handleBenchUpdate = (data: {
      operacion: string;
      duracion_ms: number;
      filas_tabla: number;
    }) => {
      setComparacion((prev) => {
        const existing = prev[data.operacion];
        if (!existing) return prev;
        return {
          ...prev,
          [data.operacion]: {
            ...existing,
            sql: {
              ...existing.sql,
              promedio_ms: data.duracion_ms,
              total_ops: existing.sql.total_ops + 1,
            },
            filas_actuales: data.filas_tabla,
          },
        };
      });
    };

    socket.on("simulation_benchmark", handleSimBench);
    socket.on("benchmark_update", handleBenchUpdate);

    return () => {
      socket.off("simulation_benchmark", handleSimBench);
      socket.off("benchmark_update", handleBenchUpdate);
    };
  }, []);

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await resetBenchmark();
      setTrendData([]);
      setHistorial([]);
      setComparacion({});
      await loadData();
    } catch (err) {
      console.error("Error reseteando benchmark:", err);
    }
    setIsResetting(false);
  };

  // Explicación contextual dinámica
  const getExplicacion = () => {
    if (filas < 10000) {
      return {
        text: "La tabla aún es pequeña. El rendimiento de SQL es aceptable.",
        color: "text-emerald-400",
        bgColor: "bg-emerald-500/10 border-emerald-500/20",
      };
    } else if (filas < 100000) {
      return {
        text: "Con más datos, SQL empieza a mostrar su limitación: cada INSERT actualiza múltiples índices.",
        color: "text-amber-400",
        bgColor: "bg-amber-500/10 border-amber-500/20",
      };
    } else {
      return {
        text: "Con más de 100.000 filas, la diferencia es clara. Redis mantiene < 1ms sin importar el volumen.",
        color: "text-red-400",
        bgColor: "bg-red-500/10 border-red-500/20",
      };
    }
  };

  const explicacion = getExplicacion();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 border border-orange-500/30">
            <Gauge size={22} className="text-orange-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Benchmark SQL vs Redis
            </h2>
            <p className="text-xs text-gray-500">
              Comparación en tiempo real de rendimiento
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-gray-500">Filas en tabla lecturas</div>
            <div className="text-lg font-bold font-mono text-white">
              {filas.toLocaleString("es-CO")}
            </div>
          </div>
          <button
            onClick={handleReset}
            disabled={isResetting}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/50 text-gray-400 hover:text-white hover:border-gray-600 transition-all text-sm disabled:opacity-50"
          >
            <RotateCcw size={14} className={isResetting ? "animate-spin" : ""} />
            Resetear
          </button>
        </div>
      </div>

      {/* ── Sección 1: Barras comparativas ── */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-5">
          <BarChart3 size={16} className="text-orange-400" />
          <h3 className="text-sm font-semibold text-gray-300">
            Rendimiento en Tiempo Real
          </h3>
        </div>

        {/* Leyenda */}
        <div className="flex items-center gap-6 mb-5 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-orange-500"></span>
            <span className="text-gray-400">PostgreSQL (SQL)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-emerald-500"></span>
            <span className="text-gray-400">Redis (referencia)</span>
          </div>
        </div>

        <div className="space-y-5">
          {Object.entries(OP_LABELS).map(([op, label]) => {
            const comp = comparacion[op];
            const sqlMs = comp?.sql?.promedio_ms || 0;
            const redisMs = comp?.redis?.referencia_ms || 0.5;
            const maxMs = Math.max(sqlMs, redisMs, 1);
            const sqlWidth = Math.min((sqlMs / maxMs) * 100, 100);
            const redisWidth = Math.min((redisMs / maxMs) * 100, 100);
            const desc = OP_DESCRIPTIONS[op];

            return (
              <div key={op}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-300 font-medium">
                    {label}
                  </span>
                  <span className="text-xs text-gray-500 font-mono">
                    {comp?.sql?.total_ops?.toLocaleString() || 0} ops
                  </span>
                </div>

                {/* Barra SQL */}
                <div className="flex items-center gap-3 mb-1.5">
                  <div className="w-16 text-xs text-gray-500 shrink-0">SQL</div>
                  <div className="flex-1 h-7 bg-gray-800/50 rounded-lg overflow-hidden relative">
                    <div
                      className="bench-bar h-full rounded-lg bg-gradient-to-r from-orange-500 to-red-500 flex items-center"
                      style={{ width: `${Math.max(sqlWidth, 2)}%` }}
                    >
                      <span className="text-xs font-mono font-bold text-white px-2 whitespace-nowrap">
                        {sqlMs.toFixed(1)} ms
                      </span>
                    </div>
                  </div>
                  <div className="w-40 text-xs text-gray-600 shrink-0 hidden md:block">
                    {desc?.sql}
                  </div>
                </div>

                {/* Barra Redis */}
                <div className="flex items-center gap-3">
                  <div className="w-16 text-xs text-gray-500 shrink-0">Redis</div>
                  <div className="flex-1 h-7 bg-gray-800/50 rounded-lg overflow-hidden relative">
                    <div
                      className="bench-bar h-full rounded-lg bg-gradient-to-r from-emerald-500 to-green-500 flex items-center"
                      style={{ width: `${Math.max(redisWidth, 2)}%` }}
                    >
                      <span className="text-xs font-mono font-bold text-white px-2 whitespace-nowrap">
                        {redisMs.toFixed(1)} ms
                      </span>
                    </div>
                  </div>
                  <div className="w-40 text-xs text-gray-600 shrink-0 hidden md:block">
                    {desc?.redis}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Sección 2: Gráfica de tendencia ── */}
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={16} className="text-orange-400" />
          <h3 className="text-sm font-semibold text-gray-300">
            Tendencia de Latencia
          </h3>
          <span className="text-xs text-gray-500">
            — INSERT vs número de filas
          </span>
        </div>

        {trendData.length < 2 ? (
          <div className="flex items-center justify-center h-52 text-gray-600 text-sm">
            Esperando datos de simulación...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="filas"
                tick={{ fontSize: 10, fill: "#6b7280" }}
                tickFormatter={(v: number) =>
                  v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)
                }
                label={{
                  value: "Filas en tabla",
                  position: "insideBottomRight",
                  offset: -5,
                  style: { fontSize: 10, fill: "#6b7280" },
                }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: "#6b7280" }}
                label={{
                  value: "ms",
                  position: "insideTopLeft",
                  style: { fontSize: 10, fill: "#6b7280" },
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(2)} ms`,
                  name === "insert_ms" ? "INSERT" : "SELECT",
                ]}
                labelFormatter={(label: number) =>
                  `${label.toLocaleString()} filas`
                }
              />
              <ReferenceLine
                y={1}
                stroke="#22c55e"
                strokeDasharray="5 5"
                label={{
                  value: "Redis < 1ms",
                  position: "right",
                  style: { fontSize: 10, fill: "#22c55e" },
                }}
              />
              <Line
                type="monotone"
                dataKey="insert_ms"
                stroke="#f97316"
                strokeWidth={2}
                dot={false}
                name="INSERT"
              />
              <Line
                type="monotone"
                dataKey="select_ms"
                stroke="#ef4444"
                strokeWidth={1.5}
                dot={false}
                name="SELECT"
                strokeDasharray="4 4"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Sección 3: Estadísticas acumuladas ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.entries(OP_LABELS).map(([op, label]) => {
          const comp = comparacion[op];
          const sqlStats = comp?.sql;

          return (
            <div key={op} className="glass-card p-5">
              <div className="flex items-center gap-2 mb-3">
                <Database size={14} className="text-orange-400" />
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {label}
                </h4>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-xs text-gray-500">Promedio</div>
                  <div className="text-lg font-bold font-mono text-orange-400">
                    {(sqlStats?.promedio_ms || 0).toFixed(1)}
                    <span className="text-xs text-gray-500 ml-1">ms</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Máximo</div>
                  <div className="text-lg font-bold font-mono text-red-400">
                    {(sqlStats?.max_ms || 0).toFixed(1)}
                    <span className="text-xs text-gray-500 ml-1">ms</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Mínimo</div>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {(sqlStats?.min_ms || 0).toFixed(1)}
                    <span className="text-xs text-gray-500 ml-1">ms</span>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Total ops</div>
                  <div className="text-lg font-bold font-mono text-gray-300">
                    {(sqlStats?.total_ops || 0).toLocaleString("es-CO")}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Sección 4: Explicación contextual ── */}
      <div className={`rounded-xl border p-5 ${explicacion.bgColor}`}>
        <div className="flex items-start gap-3">
          <Info size={18} className={`mt-0.5 shrink-0 ${explicacion.color}`} />
          <div>
            <p className={`text-sm font-medium ${explicacion.color}`}>
              {explicacion.text}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Filas actuales:{" "}
              <span className="font-mono font-bold text-gray-400">
                {filas.toLocaleString("es-CO")}
              </span>{" "}
              • Redis mantiene O(1) con{" "}
              <span className="font-mono text-emerald-500">&lt; 1ms</span>{" "}
              constante
            </p>
          </div>
        </div>
      </div>

      {/* Live indicator */}
      {latestBench && (
        <div className="flex items-center justify-center gap-2 text-xs text-gray-600">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Ciclo #{latestBench.ciclo} •{" "}
          {latestBench.lecturas_ciclo} lecturas •{" "}
          INSERT avg: {latestBench.insert_ms.toFixed(2)}ms
        </div>
      )}
    </div>
  );
}
