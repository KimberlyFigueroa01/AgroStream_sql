/**
 * FarmDetail.tsx — Detalle de finca seleccionada con métricas y gráficas.
 */

import React, { useEffect, useState, useCallback } from "react";
import { MapPin, Mountain, Clock } from "lucide-react";
import type { Finca, Sensor, Lectura, Alerta } from "../lib/types";
import { getSensores, getLecturas, getAlertasFinca, getHistorial, marcarAlertaLeida } from "../lib/api";
import { getSocket } from "../lib/socket";
import MetricCard from "./MetricCard";
import SensorChart from "./SensorChart";
import AlertPanel from "./AlertPanel";

interface FarmDetailProps {
  finca: Finca;
  lecturas: Lectura[];
}

export default function FarmDetail({ finca, lecturas }: FarmDetailProps) {
  const [sensores, setSensores] = useState<Sensor[]>([]);
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [sensorHistorial, setSensorHistorial] = useState<
    Record<string, { valor: number; timestamp: string }[]>
  >({});
  const [selectedSensorTipo, setSelectedSensorTipo] = useState<string>("temperatura");

  // Cargar sensores y alertas al seleccionar finca
  useEffect(() => {
    getSensores(finca.id).then(setSensores).catch(console.error);
    getAlertasFinca(finca.id).then(setAlertas).catch(console.error);
  }, [finca.id]);

  // Cargar historial para el sensor seleccionado
  useEffect(() => {
    if (!sensores.length) return;
    // Encontrar el primer sensor del tipo seleccionado
    const sensor = sensores.find((s) => s.tipo === selectedSensorTipo);
    if (!sensor) return;

    getHistorial(finca.id, sensor.id)
      .then((data) => {
        setSensorHistorial((prev) => ({
          ...prev,
          [selectedSensorTipo]: data,
        }));
      })
      .catch(console.error);
  }, [finca.id, sensores, selectedSensorTipo]);

  // WebSocket: escuchar nuevas alertas
  useEffect(() => {
    const socket = getSocket();

    const handleAlerts = (newAlertas: Alerta[]) => {
      const fincaAlertas = newAlertas.filter((a) => a.finca_id === finca.id);
      if (fincaAlertas.length > 0) {
        setAlertas((prev) => [...fincaAlertas, ...prev].slice(0, 50));
      }
    };

    socket.on("sensor_alerts", handleAlerts);
    return () => { socket.off("sensor_alerts", handleAlerts); };
  }, [finca.id]);

  // WebSocket: actualizar historial en tiempo real
  useEffect(() => {
    const socket = getSocket();

    const handleReading = (data: {
      finca_id: string;
      tipo: string;
      valor: number;
      timestamp: string;
    }) => {
      if (data.finca_id !== finca.id) return;

      setSensorHistorial((prev) => {
        const existing = prev[data.tipo] || [];
        const updated = [
          { valor: data.valor, timestamp: data.timestamp },
          ...existing,
        ].slice(0, 60);
        return { ...prev, [data.tipo]: updated };
      });
    };

    socket.on("sensor_reading", handleReading);
    return () => { socket.off("sensor_reading", handleReading); };
  }, [finca.id]);

  const handleMarcarLeida = useCallback(async (alertaId: string) => {
    try {
      await marcarAlertaLeida(alertaId);
      setAlertas((prev) =>
        prev.map((a) => (a.id === alertaId ? { ...a, leida: true } : a))
      );
    } catch (err) {
      console.error("Error marcando alerta:", err);
    }
  }, []);

  // Tipos de sensor disponibles
  const tiposDisponibles = [...new Set(sensores.map((s) => s.tipo))];

  const TIPO_LABELS: Record<string, string> = {
    temperatura: "Temp.",
    humedad: "Hum.",
    co2: "CO₂",
    humedad_suelo: "Suelo",
    radiacion: "Rad.",
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="glass-card p-5">
        <h2 className="text-xl font-bold text-white mb-2">{finca.nombre}</h2>
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span className="flex items-center gap-1.5">
            <MapPin size={14} />
            {finca.lat.toFixed(4)}°N, {Math.abs(finca.lon).toFixed(4)}°W
          </span>
          <span className="flex items-center gap-1.5">
            <Mountain size={14} />
            {finca.altitud_m} m.s.n.m.
          </span>
          <span className="flex items-center gap-1.5">
            <Clock size={14} />
            {sensores.length} sensores
          </span>
        </div>
      </div>

      {/* Métricas actuales */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {lecturas.map((l) => (
          <MetricCard
            key={l.tipo}
            tipo={l.tipo}
            valor={l.valor}
            unidad={l.unidad}
            timestamp={l.timestamp}
          />
        ))}
      </div>

      {/* Gráficas de historial */}
      <div className="glass-card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-300">
            Historial de Sensor
          </h3>
          <div className="flex gap-1">
            {tiposDisponibles.map((tipo) => (
              <button
                key={tipo}
                onClick={() => setSelectedSensorTipo(tipo)}
                className={`text-xs px-3 py-1.5 rounded-lg transition-all ${
                  selectedSensorTipo === tipo
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                }`}
              >
                {TIPO_LABELS[tipo] || tipo}
              </button>
            ))}
          </div>
        </div>
        <SensorChart
          data={sensorHistorial[selectedSensorTipo] || []}
          tipo={selectedSensorTipo}
          unidad={
            lecturas.find((l) => l.tipo === selectedSensorTipo)?.unidad || ""
          }
        />
      </div>

      {/* Alertas */}
      <AlertPanel alertas={alertas} onMarcarLeida={handleMarcarLeida} />
    </div>
  );
}
