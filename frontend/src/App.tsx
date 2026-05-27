import React, { useEffect, useState, useCallback } from "react";
import FarmList from "./components/FarmList";
import FarmDetail from "./components/FarmDetail";
import BenchmarkPanel from "./components/BenchmarkPanel";
import AddFincaModal from "./components/AddFincaModal";
import { getFincas, getLecturas } from "./lib/api";
import { getSocket } from "./lib/socket";
import type { Finca, Lectura } from "./lib/types";

export default function App() {
  const [fincas, setFincas] = useState<Finca[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [lecturasPorFinca, setLecturasPorFinca] = useState<Record<string, Lectura[]>>({});
  const [isAddOpen, setIsAddOpen] = useState(false);

  useEffect(() => {
    loadFincas();
    const socket = getSocket();

    const handleReading = (data: Lectura & { finca_id: string }) => {
      setLecturasPorFinca((prev) => {
        const cur = prev[data.finca_id] || [];
        // replace existing reading of same tipo or prepend
        const filtered = cur.filter((r) => r.tipo !== data.tipo);
        const next = [
          { tipo: data.tipo, valor: data.valor, unidad: data.unidad, timestamp: data.timestamp },
          ...filtered,
        ];
        return { ...prev, [data.finca_id]: next };
      });
    };

    socket.on("sensor_reading", handleReading);
    return () => {
      socket.off("sensor_reading", handleReading);
    };
  }, []);

  const loadFincas = useCallback(async () => {
    try {
      const data = await getFincas();
      setFincas(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      console.error("Error cargando fincas:", err);
    }
  }, [selectedId]);

  useEffect(() => {
    if (!selectedId) return;
    // load lecturas for selected finca
    (async () => {
      try {
        const lect = await getLecturas(selectedId);
        setLecturasPorFinca((prev) => ({ ...prev, [selectedId]: lect }));
      } catch (err) {
        console.error("Error cargando lecturas:", err);
      }
    })();
  }, [selectedId]);

  const handleSelect = (id: string) => {
    setSelectedId(id);
  };

  const selectedFinca = fincas.find((f) => f.id === selectedId) || null;
  const lecturasForSelected = selectedId ? lecturasPorFinca[selectedId] || [] : [];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">AgroStream — SQL Demo</h1>
          <button
            onClick={() => setIsAddOpen(true)}
            className="text-sm px-3 py-2 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
          >
            Agregar finca
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <aside className="lg:col-span-1">
            <FarmList
              fincas={fincas}
              selectedId={selectedId}
              onSelect={handleSelect}
              lecturasPorFinca={lecturasPorFinca}
            />
          </aside>

          <main className="lg:col-span-3 space-y-6">
            <BenchmarkPanel />

            {selectedFinca ? (
              <FarmDetail finca={selectedFinca} lecturas={lecturasForSelected} />
            ) : (
              <div className="glass-card p-6">Selecciona una finca para ver detalles.</div>
            )}
          </main>
        </div>
      </div>

      <AddFincaModal
        open={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onCreated={(finca) => {
          setFincas((prev) => [...prev, finca]);
          setSelectedId(finca.id);
        }}
      />
    </div>
  );
}
