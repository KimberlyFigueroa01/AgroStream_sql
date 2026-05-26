/**
 * FarmList.tsx — Lista de fincas con estado en tiempo real.
 */

import React from "react";
import { MapPin, Mountain, Radio } from "lucide-react";
import type { Finca, Lectura } from "../lib/types";

interface FarmListProps {
  fincas: Finca[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  lecturasPorFinca: Record<string, Lectura[]>;
}

export default function FarmList({
  fincas,
  selectedId,
  onSelect,
  lecturasPorFinca,
}: FarmListProps) {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-bold text-white flex items-center gap-2 px-1">
        <Radio size={18} className="text-emerald-400 status-dot" />
        Fincas Activas
      </h2>

      {fincas.map((finca) => {
        const isSelected = finca.id === selectedId;
        const lecturas = lecturasPorFinca[finca.id] || [];
        const tempLectura = lecturas.find((l) => l.tipo === "temperatura");
        const humLectura = lecturas.find((l) => l.tipo === "humedad");

        return (
          <button
            key={finca.id}
            onClick={() => onSelect(finca.id)}
            className={`w-full text-left rounded-xl p-4 transition-all duration-300 border ${
              isSelected
                ? "glass-card border-emerald-500/40 glow-green"
                : "bg-gray-900/30 border-gray-800/50 hover:bg-gray-900/50 hover:border-gray-700/50"
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold text-white text-sm">
                {finca.nombre}
              </h3>
              {isSelected && (
                <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full">
                  Activa
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs text-gray-400 mb-3">
              <span className="flex items-center gap-1">
                <MapPin size={12} />
                {finca.lat.toFixed(2)}°, {finca.lon.toFixed(2)}°
              </span>
              <span className="flex items-center gap-1">
                <Mountain size={12} />
                {finca.altitud_m}m
              </span>
            </div>

            {/* Mini métricas */}
            {lecturas.length > 0 && (
              <div className="flex gap-4 text-xs">
                {tempLectura && (
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-orange-400"></span>
                    <span className="text-gray-300 font-mono">
                      {tempLectura.valor.toFixed(1)}°C
                    </span>
                  </div>
                )}
                {humLectura && (
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                    <span className="text-gray-300 font-mono">
                      {humLectura.valor.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
