/**
 * SensorChart.tsx — Gráfica de historial por sensor usando Recharts.
 */

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface DataPoint {
  valor: number;
  timestamp: string;
}

interface SensorChartProps {
  data: DataPoint[];
  tipo: string;
  unidad: string;
  color?: string;
}

const COLOR_MAP: Record<string, string> = {
  temperatura: "#f97316",
  humedad: "#3b82f6",
  co2: "#8b5cf6",
  humedad_suelo: "#10b981",
  radiacion: "#eab308",
};

const LABEL_MAP: Record<string, string> = {
  temperatura: "Temperatura",
  humedad: "Humedad",
  co2: "CO₂",
  humedad_suelo: "Humedad Suelo",
  radiacion: "Radiación",
};

export default function SensorChart({
  data,
  tipo,
  unidad,
  color,
}: SensorChartProps) {
  const lineColor = color || COLOR_MAP[tipo] || "#22c55e";
  const label = LABEL_MAP[tipo] || tipo;

  // Invertir para que el más reciente esté a la derecha
  const chartData = [...data].reverse().map((d, i) => ({
    idx: i,
    valor: d.valor,
    time: new Date(d.timestamp).toLocaleTimeString("es-CO", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }),
  }));

  if (chartData.length === 0) {
    return (
      <div className="glass-card p-6 flex items-center justify-center h-48">
        <span className="text-gray-500 text-sm">
          Sin datos de {label} aún...
        </span>
      </div>
    );
  }

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold text-gray-300 mb-3">
        {label}{" "}
        <span className="text-gray-500 font-normal">({unidad})</span>
      </h3>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 10, fill: "#6b7280" }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#6b7280" }}
            domain={["auto", "auto"]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(value: number) => [
              `${value.toFixed(2)} ${unidad}`,
              label,
            ]}
          />
          <Line
            type="monotone"
            dataKey="valor"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: lineColor }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
