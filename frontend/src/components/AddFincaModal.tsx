import React, { useEffect, useMemo, useState } from "react";
import { X, MapPin, Search, Crosshair } from "lucide-react";
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { crearFinca } from "../lib/api";
import type { Finca } from "../lib/types";

const defaultPosition: [number, number] = [5.5353, -73.3621];

const iconRetinaUrl = new URL(
  "leaflet/dist/images/marker-icon-2x.png",
  import.meta.url
).toString();
const iconUrl = new URL(
  "leaflet/dist/images/marker-icon.png",
  import.meta.url
).toString();
const shadowUrl = new URL(
  "leaflet/dist/images/marker-shadow.png",
  import.meta.url
).toString();

L.Icon.Default.mergeOptions({ iconRetinaUrl, iconUrl, shadowUrl });

interface GeocodeResult {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country?: string;
  admin1?: string;
  admin2?: string;
}

interface AddFincaModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (finca: Finca) => void;
}

function LocationPicker({
  value,
  onChange,
}: {
  value: { lat: number; lon: number } | null;
  onChange: (next: { lat: number; lon: number }) => void;
}) {
  useMapEvents({
    click(e) {
      onChange({ lat: e.latlng.lat, lon: e.latlng.lng });
    },
  });

  if (!value) {
    return null;
  }

  return <Marker position={[value.lat, value.lon]} />;
}

async function fetchElevation(lat: number, lon: number): Promise<number | null> {
  try {
    const url = `https://api.open-meteo.com/v1/elevation?latitude=${lat}&longitude=${lon}`;
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    const elev = Array.isArray(data?.elevation) ? data.elevation[0] : null;
    return typeof elev === "number" ? Math.round(elev) : null;
  } catch {
    return null;
  }
}

async function searchAddress(query: string): Promise<GeocodeResult[]> {
  const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(
    query
  )}&count=5&language=es&format=json`;
  const res = await fetch(url);
  if (!res.ok) return [];
  const data = await res.json();
  return Array.isArray(data?.results) ? data.results : [];
}

export default function AddFincaModal({ open, onClose, onCreated }: AddFincaModalProps) {
  const [mode, setMode] = useState<"coords" | "address" | "map">("coords");
  const [nombre, setNombre] = useState("");
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const [altitud, setAltitud] = useState("");
  const [ciudad, setCiudad] = useState<string | null>(null);
  const [departamento, setDepartamento] = useState<string | null>(null);
  const [addressQuery, setAddressQuery] = useState("");
  const [addressResults, setAddressResults] = useState<GeocodeResult[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mapValue = useMemo(() => {
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    if (Number.isFinite(latNum) && Number.isFinite(lonNum)) {
      return { lat: latNum, lon: lonNum };
    }
    return null;
  }, [lat, lon]);

  useEffect(() => {
    if (!open) return;
    setError(null);
  }, [open]);

  const handleSelectResult = async (result: GeocodeResult) => {
    setLat(result.latitude.toFixed(6));
    setLon(result.longitude.toFixed(6));
    setCiudad(result.name);
    setDepartamento(result.admin1 || null);
    const elev = await fetchElevation(result.latitude, result.longitude);
    if (elev !== null) {
      setAltitud(String(elev));
    }
  };

  const handleMapChange = async (next: { lat: number; lon: number }) => {
    setLat(next.lat.toFixed(6));
    setLon(next.lon.toFixed(6));
    const elev = await fetchElevation(next.lat, next.lon);
    if (elev !== null) {
      setAltitud(String(elev));
    }
  };

  const handleSearch = async () => {
    if (!addressQuery.trim()) return;
    setAddressResults(await searchAddress(addressQuery.trim()));
  };

  const handleSubmit = async () => {
    setError(null);
    const latNum = parseFloat(lat);
    const lonNum = parseFloat(lon);
    if (!nombre.trim()) {
      setError("Nombre es requerido");
      return;
    }
    if (!Number.isFinite(latNum) || !Number.isFinite(lonNum)) {
      setError("Latitud y longitud son requeridas");
      return;
    }

    const altNum = altitud ? parseFloat(altitud) : undefined;

    setIsSaving(true);
    try {
      const finca = await crearFinca({
        nombre: nombre.trim(),
        lat: latNum,
        lon: lonNum,
        altitud_m: Number.isFinite(altNum) ? altNum : undefined,
        ciudad,
        departamento,
      });
      onCreated(finca);
      onClose();
      setNombre("");
      setLat("");
      setLon("");
      setAltitud("");
      setAddressQuery("");
      setAddressResults([]);
    } catch (err: any) {
      setError(err?.message || "Error creando finca");
    } finally {
      setIsSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-3xl glass-card p-6 relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-200"
          aria-label="Cerrar"
        >
          <X size={18} />
        </button>

        <h2 className="text-lg font-semibold text-white mb-4">Agregar finca</h2>

        <div className="flex gap-2 mb-4 text-xs">
          <button
            onClick={() => setMode("coords")}
            className={`px-3 py-1.5 rounded-lg border transition-all ${
              mode === "coords"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-gray-700/60 text-gray-400 hover:text-gray-200"
            }`}
          >
            Coordenadas
          </button>
          <button
            onClick={() => setMode("address")}
            className={`px-3 py-1.5 rounded-lg border transition-all ${
              mode === "address"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-gray-700/60 text-gray-400 hover:text-gray-200"
            }`}
          >
            Direccion
          </button>
          <button
            onClick={() => setMode("map")}
            className={`px-3 py-1.5 rounded-lg border transition-all ${
              mode === "map"
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "border-gray-700/60 text-gray-400 hover:text-gray-200"
            }`}
          >
            Mapa
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-400">Nombre</label>
            <input
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              className="mt-1 w-full rounded-lg bg-gray-900/60 border border-gray-700/60 px-3 py-2 text-sm text-gray-100"
              placeholder="Finca La Esperanza"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Altitud (m)</label>
            <input
              value={altitud}
              onChange={(e) => setAltitud(e.target.value)}
              className="mt-1 w-full rounded-lg bg-gray-900/60 border border-gray-700/60 px-3 py-2 text-sm text-gray-100"
              placeholder="2600"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Latitud</label>
            <input
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              className="mt-1 w-full rounded-lg bg-gray-900/60 border border-gray-700/60 px-3 py-2 text-sm text-gray-100"
              placeholder="5.5236"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400">Longitud</label>
            <input
              value={lon}
              onChange={(e) => setLon(e.target.value)}
              className="mt-1 w-full rounded-lg bg-gray-900/60 border border-gray-700/60 px-3 py-2 text-sm text-gray-100"
              placeholder="-73.1050"
            />
          </div>
        </div>

        {mode === "address" && (
          <div className="mb-4">
            <label className="text-xs text-gray-400">Direccion o lugar</label>
            <div className="mt-1 flex gap-2">
              <input
                value={addressQuery}
                onChange={(e) => setAddressQuery(e.target.value)}
                className="flex-1 rounded-lg bg-gray-900/60 border border-gray-700/60 px-3 py-2 text-sm text-gray-100"
                placeholder="Villa de Leyva, Boyaca"
              />
              <button
                onClick={handleSearch}
                className="px-3 py-2 text-sm rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
              >
                <Search size={16} />
              </button>
            </div>
            {addressResults.length > 0 && (
              <div className="mt-2 max-h-48 overflow-y-auto border border-gray-800/60 rounded-lg">
                {addressResults.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => handleSelectResult(result)}
                    className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-800/60"
                  >
                    <MapPin size={14} className="inline mr-2 text-emerald-400" />
                    {result.name} {result.admin1 ? `- ${result.admin1}` : ""} {result.country ? `(${result.country})` : ""}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {mode === "map" && (
          <div className="mb-4">
            <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
              <Crosshair size={14} />
              Click en el mapa para seleccionar ubicacion
            </div>
            <div className="h-64 rounded-lg overflow-hidden border border-gray-800/60">
              <MapContainer
                center={mapValue ? [mapValue.lat, mapValue.lon] : defaultPosition}
                zoom={12}
                className="h-full w-full"
              >
                <TileLayer
                  attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <LocationPicker value={mapValue} onChange={handleMapChange} />
              </MapContainer>
            </div>
          </div>
        )}

        {error && <div className="text-sm text-red-400 mb-3">{error}</div>}

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-3 py-2 text-sm rounded-lg border border-gray-700/60 text-gray-300"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSaving}
            className="px-3 py-2 text-sm rounded-lg bg-emerald-500/30 text-emerald-200 border border-emerald-500/50 disabled:opacity-50"
          >
            {isSaving ? "Guardando..." : "Crear finca"}
          </button>
        </div>
      </div>
    </div>
  );
}
