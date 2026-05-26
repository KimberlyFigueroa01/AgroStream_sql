/**
 * AlertPanel.tsx — Panel de alertas con niveles y animaciones.
 */

import React from "react";
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Bell,
  CheckCircle,
} from "lucide-react";
import type { Alerta } from "../lib/types";

interface AlertPanelProps {
  alertas: Alerta[];
  onMarcarLeida?: (id: string) => void;
}

const NIVEL_STYLES: Record<
  string,
  { bg: string; border: string; icon: React.ElementType; iconColor: string }
> = {
  critico: {
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    icon: AlertTriangle,
    iconColor: "text-red-400",
  },
  advertencia: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    icon: AlertCircle,
    iconColor: "text-amber-400",
  },
  info: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    icon: Info,
    iconColor: "text-blue-400",
  },
};

export default function AlertPanel({ alertas, onMarcarLeida }: AlertPanelProps) {
  if (alertas.length === 0) {
    return (
      <div className="glass-card p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell size={18} className="text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-300">Alertas</h3>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-gray-500">
          <CheckCircle size={32} className="mb-2 text-emerald-500/50" />
          <p className="text-sm">Sin alertas activas</p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bell size={18} className="text-amber-400" />
          <h3 className="text-sm font-semibold text-gray-300">Alertas</h3>
        </div>
        <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full">
          {alertas.filter((a) => !a.leida).length} sin leer
        </span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
        {alertas.map((alerta) => {
          const style = NIVEL_STYLES[alerta.nivel] || NIVEL_STYLES.info;
          const Icon = style.icon;

          return (
            <div
              key={alerta.id}
              className={`flex items-start gap-3 p-3 rounded-lg border ${style.bg} ${style.border} ${
                alerta.leida ? "opacity-50" : ""
              } animate-slide-up transition-opacity`}
            >
              <Icon size={16} className={`mt-0.5 shrink-0 ${style.iconColor}`} />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-200 leading-relaxed">
                  {alerta.mensaje}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {alerta.finca_nombre}
                  </span>
                  <span className="text-xs text-gray-600">•</span>
                  <span className="text-xs text-gray-500 font-mono">
                    {new Date(alerta.timestamp).toLocaleTimeString("es-CO", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>
              {!alerta.leida && onMarcarLeida && (
                <button
                  onClick={() => onMarcarLeida(alerta.id)}
                  className="shrink-0 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                  title="Marcar como leída"
                >
                  ✓
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
