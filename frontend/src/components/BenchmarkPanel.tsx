/**
 * BenchmarkPanel.tsx — Panel comparativo PostgreSQL vs Redis
 * 
 * Muestra dos gráficos separados (escalas independientes) para una mejor comprensión.
 */

import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Database, Zap, Info } from "lucide-react";
import { getSocket } from "../lib/socket";
import { getFilasLecturas, resetBenchmark } from "../lib/api";
import type { SimulationBenchmarkEvent, BenchmarkUpdate } from "../lib/types";

const MAX_DATA_POINTS = 30;

interface DataPoint {
  timestamp: string;
  postgres_ms: number;
  redis_ms: number;
}

interface Statistics {
  count: number;
  promedio_ms: number;
  min_ms: number;
  max_ms: number;
}

const toNumber = (value: any): number => {
  if (typeof value === 'number') return value;
  if (typeof value === 'boolean') return value ? 1 : 0;
  if (typeof value === 'string') {
    const parsed = parseFloat(value);
    return isNaN(parsed) ? 0 : parsed;
  }
  return 0;
};

export default function BenchmarkPanel() {
  const [postgresStats, setPostgresStats] = useState<Statistics>({ count: 0, promedio_ms: 0, min_ms: 0, max_ms: 0 });
  const [redisStats, setRedisStats] = useState<Statistics>({ count: 0, promedio_ms: 0, min_ms: 0, max_ms: 0 });
  const [chartData, setChartData] = useState<DataPoint[]>([]);
  const [filas, setFilas] = useState<number>(0);
  const [isResetting, setIsResetting] = useState(false);
  const [hasRedisData, setHasRedisData] = useState(false);

  // Cargar filas iniciales
  useEffect(() => {
    const loadFilas = async () => {
      try {
        const res = await getFilasLecturas();
        setFilas(typeof res === 'number' ? res : res?.filas_lecturas ?? 0);
      } catch (err) { console.error(err); }
    };
    loadFilas();
    const interval = setInterval(loadFilas, 10000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket: benchmark_update
  useEffect(() => {
    const socket = getSocket();
    let postgresValues: number[] = [];
    let redisValues: number[] = [];

    const handleUpdate = (data: BenchmarkUpdate) => {
      const duration = toNumber(data.duracion_ms);
      if (data.db === "postgresql") {
        postgresValues.push(duration);
        setPostgresStats(calculateStats(postgresValues));
      } else if (data.db === "redis") {
        redisValues.push(duration);
        setRedisStats(calculateStats(redisValues));
        setHasRedisData(true);
      }

      const timestamp = new Date(data.timestamp).toLocaleTimeString("es-CO", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });

      setChartData((prev) => {
        const newPoint = { timestamp, postgres_ms: data.db === "postgresql" ? duration : (prev[prev.length-1]?.postgres_ms || 0), redis_ms: data.db === "redis" ? duration : (prev[prev.length-1]?.redis_ms || 0) };
        const newData = [...prev, newPoint];
        return newData.slice(-MAX_DATA_POINTS);
      });
    };

    socket.on("benchmark_update", handleUpdate);
    return () => { socket.off("benchmark_update", handleUpdate); };
  }, []);

  // simulation_benchmark para actualizar filas
  useEffect(() => {
    const socket = getSocket();
    const handleSimBench = (data: SimulationBenchmarkEvent) => { setFilas(data.filas_lecturas ?? 0); };
    socket.on("simulation_benchmark", handleSimBench);
    return () => { socket.off("simulation_benchmark", handleSimBench); };
  }, []);

  const calculateStats = (values: number[]): Statistics => {
    if (!values.length) return { count: 0, promedio_ms: 0, min_ms: 0, max_ms: 0 };
    return {
      count: values.length,
      promedio_ms: Number((values.reduce((a,b) => a+b, 0) / values.length).toFixed(2)),
      min_ms: Number(Math.min(...values).toFixed(2)),
      max_ms: Number(Math.max(...values).toFixed(2)),
    };
  };

  const handleReset = async () => {
    setIsResetting(true);
    try {
      await resetBenchmark();
      setChartData([]);
      setPostgresStats({ count: 0, promedio_ms: 0, min_ms: 0, max_ms: 0 });
      setRedisStats({ count: 0, promedio_ms: 0, min_ms: 0, max_ms: 0 });
      setHasRedisData(false);
      const res = await getFilasLecturas();
      setFilas(typeof res === 'number' ? res : res?.filas_lecturas ?? 0);
    } catch (err) { console.error(err); }
    setIsResetting(false);
  };

  const ratio = postgresStats.promedio_ms > 0 && redisStats.promedio_ms > 0
    ? (parseFloat(String(postgresStats.promedio_ms)) / parseFloat(String(redisStats.promedio_ms))).toFixed(1)
    : null;

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Benchmark de Rendimiento</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">PostgreSQL (disco) vs Redis (memoria)</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-xs text-gray-500">Lecturas almacenadas</div>
              <div className="text-xl font-mono font-bold text-gray-800 dark:text-gray-200">{filas.toLocaleString()}</div>
            </div>
            <button
              onClick={handleReset}
              disabled={isResetting}
              className="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition disabled:opacity-50"
            >
              {isResetting ? "Limpiando..." : "Limpiar gráficos"}
            </button>
          </div>
        </div>

        {/* Tarjetas de estadísticas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* PostgreSQL Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-5 border-l-4 border-blue-500">
            <div className="flex items-center gap-2 mb-3">
              <Database size={18} className="text-blue-500" />
              <h3 className="font-medium text-gray-700 dark:text-gray-300">PostgreSQL (Base de datos en disco)</h3>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><div className="text-xs text-gray-500">Promedio</div><div className="text-xl font-bold text-blue-600">{parseFloat(String(postgresStats.promedio_ms)).toFixed(1)} ms</div></div>
              <div><div className="text-xs text-gray-500">Mínimo</div><div className="text-lg font-medium">{parseFloat(String(postgresStats.min_ms)).toFixed(1)} ms</div></div>
              <div><div className="text-xs text-gray-500">Máximo</div><div className="text-lg font-medium">{parseFloat(String(postgresStats.max_ms)).toFixed(1)} ms</div></div>
            </div>
            <div className="text-xs text-gray-400 mt-2">Muestras: {postgresStats.count}</div>
          </div>

          {/* Redis Card */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-5 border-l-4 border-green-500">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={18} className="text-green-500" />
              <h3 className="font-medium text-gray-700 dark:text-gray-300">Redis (Base de datos en memoria)</h3>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div><div className="text-xs text-gray-500">Promedio</div><div className="text-xl font-bold text-green-600">{parseFloat(String(redisStats.promedio_ms)).toFixed(2)} ms</div></div>
              <div><div className="text-xs text-gray-500">Mínimo</div><div className="text-lg font-medium">{parseFloat(String(redisStats.min_ms)).toFixed(2)} ms</div></div>
              <div><div className="text-xs text-gray-500">Máximo</div><div className="text-lg font-medium">{parseFloat(String(redisStats.max_ms)).toFixed(2)} ms</div></div>
            </div>
            <div className="text-xs text-gray-400 mt-2">Muestras: {redisStats.count} {!hasRedisData && <span className="text-yellow-600">(Esperando datos...)</span>}</div>
          </div>
        </div>

        {/* Explicación contextual */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-8">
          <div className="flex gap-3">
            <Info size={20} className="text-blue-600 dark:text-blue-400 shrink-0 mt-0.5" />
            <div className="text-sm text-gray-700 dark:text-gray-300">
              <span className="font-medium">¿Por qué la diferencia?</span> Redis opera completamente en memoria RAM, lo que permite tiempos de respuesta de milisegundos. PostgreSQL escribe en disco y mantiene integridad transaccional (ACID), siendo más lento pero más seguro para datos históricos. En este benchmark, Redis es <strong>{ratio || "—"} veces más rápido</strong> en promedio para operaciones de escritura.
            </div>
          </div>
        </div>

        {/* Gráficos separados */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Gráfico PostgreSQL */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-5">
            <h3 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-500"></span>
              PostgreSQL (latencia de escritura)
            </h3>
            <p className="text-xs text-gray-500 mb-4">Cada punto representa la duración de un INSERT en milisegundos.</p>
            {chartData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-gray-400">Esperando datos de simulación...</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis 
                    label={{ value: "ms", angle: -90, position: "insideLeft", style: { fontSize: 11 } }}
                    domain={[0, (dataMax: number) => Math.ceil(dataMax * 1.1)]}
                    tickCount={6}
                  />
                  <Tooltip formatter={(val: number) => [`${val.toFixed(2)} ms`, "PostgreSQL"]} />
                  <Line type="monotone" dataKey="postgres_ms" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Gráfico Redis */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-5">
            <h3 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-2 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-green-500"></span>
              Redis (latencia de escritura)
            </h3>
            <p className="text-xs text-gray-500 mb-4">Cada punto representa la duración de una operación HSET o LPUSH en milisegundos.</p>
            {!hasRedisData ? (
              <div className="h-64 flex items-center justify-center text-gray-400">Esperando conexión con Redis...</div>
            ) : chartData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-gray-400">Esperando datos de simulación...</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                  <YAxis 
                    label={{ value: "ms", angle: -90, position: "insideLeft", style: { fontSize: 11 } }}
                    domain={[0, 20]}
                    tickCount={6}
                  />
                  <Tooltip formatter={(val: number) => [`${val.toFixed(3)} ms`, "Redis"]} />
                  <Line type="monotone" dataKey="redis_ms" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Resumen adicional de ratio de mejora */}
        {ratio && (
          <div className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
            En promedio, Redis es <strong className="text-green-600 dark:text-green-400">{ratio}x más rápido</strong> que PostgreSQL para escritura de datos en este escenario.
          </div>
        )}
      </div>
    </div>
  );
}