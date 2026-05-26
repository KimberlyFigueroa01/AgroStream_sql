/**
 * MetricCard.tsx — Tarjeta de métrica individual con animación de actualización.
 */

import React, { useEffect, useRef, useState } from "react";
import {
  Thermometer,
  Droplets,
  Wind,
  Sun,
  Sprout,
  type LucideIcon,
} from "lucide-react";

interface MetricCardProps {
  tipo: string;
  valor: number;
  unidad: string;
  timestamp?: string;
  anomalia?: boolean;
}

const ICON_MAP: Record<string, LucideIcon> = {
  temperatura: Thermometer,
  humedad: Droplets,
  co2: Wind,
  humedad_suelo: Sprout,
  radiacion: Sun,
};

const COLOR_MAP: Record<string, string> = {
  temperatura: "from-orange-500/20 to-red-500/20 border-orange-500/30",
  humedad: "from-blue-500/20 to-cyan-500/20 border-blue-500/30",
  co2: "from-purple-500/20 to-indigo-500/20 border-purple-500/30",
  humedad_suelo: "from-emerald-500/20 to-green-500/20 border-emerald-500/30",
  radiacion: "from-yellow-500/20 to-amber-500/20 border-yellow-500/30",
};

const ICON_COLOR_MAP: Record<string, string> = {
  temperatura: "text-orange-400",
  humedad: "text-blue-400",
  co2: "text-purple-400",
  humedad_suelo: "text-emerald-400",
  radiacion: "text-yellow-400",
};

const LABEL_MAP: Record<string, string> = {
  temperatura: "Temperatura",
  humedad: "Humedad",
  co2: "CO₂",
  humedad_suelo: "Humedad Suelo",
  radiacion: "Radiación",
};

export default function MetricCard({
  tipo,
  valor,
  unidad,
  timestamp,
  anomalia,
}: MetricCardProps) {
  const [updated, setUpdated] = useState(false);
  const prevValor = useRef(valor);

  useEffect(() => {
    if (prevValor.current !== valor) {
      setUpdated(true);
      prevValor.current = valor;
      const timer = setTimeout(() => setUpdated(false), 300);
      return () => clearTimeout(timer);
    }
  }, [valor]);

  const Icon = ICON_MAP[tipo] || Thermometer;
  const colors = COLOR_MAP[tipo] || COLOR_MAP.temperatura;
  const iconColor = ICON_COLOR_MAP[tipo] || "text-gray-400";
  const label = LABEL_MAP[tipo] || tipo;

  const timeStr = timestamp
    ? new Date(timestamp).toLocaleTimeString("es-CO", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "";

  return (
    <div
      className={`relative overflow-hidden rounded-xl border bg-gradient-to-br ${colors} p-4 transition-all duration-300 hover:scale-[1.02] ${
        updated ? "metric-update" : ""
      } ${anomalia ? "glow-red ring-1 ring-red-500/50" : ""}`}
    >
      {anomalia && (
        <div className="absolute top-2 right-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </span>
        </div>
      )}

      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg bg-gray-800/50 ${iconColor}`}>
          <Icon size={20} />
        </div>
        <span className="text-sm font-medium text-gray-300">{label}</span>
      </div>

      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-white tabular-nums">
          {typeof valor === "number" ? valor.toFixed(1) : valor}
        </span>
        <span className="text-sm text-gray-400">{unidad}</span>
      </div>

      {timeStr && (
        <div className="mt-2 text-xs text-gray-500 font-mono">{timeStr}</div>
      )}
    </div>
  );
}
