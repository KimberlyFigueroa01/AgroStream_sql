# AgroStream-SQL: Arquitectura Híbrida (PostgreSQL + Redis)

Este proyecto implementa un sistema de monitoreo agrícola con **arquitectura híbrida** que mide y compara el rendimiento de PostgreSQL y Redis en tiempo real.

## 🏗️ Arquitectura Híbrida

### ¿Por qué dos bases de datos?

**PostgreSQL** es perfecto para:
- Almacenamiento durabilidad de históricos completos
- Consultas complejas con JOINs
- Datos transaccionales críticos

**Redis** es perfecto para:
- Operaciones ultra-rápidas en caché (ms → µs)
- Streaming de datos en tiempo real
- Estado vivo de sensores

### Flujo de Datos en Tiempo Real

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIMULADOR DE SENSORES                         │
│              (simulation/sensor_virtual.py)                       │
│         Genera lecturas cada INTERVALO_LECTURA_S segundos        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Lectura virtual: temperatura, humedad, etc.
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│              INGESTA HÍBRIDA (IngestaService)                    │
│    Recibe: lectura de sensor | Retorna: tiempos de ambas BDs    │
└────────────────┬──────────────────────────────┬─────────────────┘
                 │                              │
        ┌────────↓─────────┐         ┌──────────↓────────┐
        │   PostgreSQL     │         │      Redis        │
        ├─────────────────┤         ├────────────────────┤
        │ INSERT lecturas │         │ HSET sensor_estado │
        │ SELECT por JOIN │         │ LPUSH historial    │
        │ 200-300 ms      │         │ 0.5-1 ms           │
        └────────┬────────┘         └────────┬───────────┘
                 │                          │
                 └──────────┬────────────────┘
                            │ Duraciones medidas
                            ↓
          ┌─────────────────────────────────┐
          │ MetricaBenchmark (PostgreSQL)    │
          │ Tabla de auditoría de tiempos    │
          │ operacion, duracion_ms, timestamp│
          └────────────┬────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │ WebSocket EventEmitter      │
        │ (benchmark_update eventos)  │
        └─────────────┬───────────────┘
                      │ Socket.IO events con campo "db"
                      ↓
        ┌─────────────────────────────┐
        │    FRONTEND (React)         │
        │  BenchmarkPanel.tsx         │
        │  - Gráficos en tiempo real  │
        │  - Estadísticas en vivo     │
        │  - Ratio PostgreSQL/Redis   │
        └─────────────────────────────┘
```

## 📊 Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# ────── PostgreSQL ──────
DATABASE_URL=postgresql://neondb_owner:npg_KAwvptrW6Q0i@ep-damp-field-aqchkfoj.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require

# ────── Redis (Opcional, gracefully degrades si no está disponible) ──────
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=             # Vacío si no requiere autenticación

# ────── Simulación ──────
INTERVALO_LECTURA_S=5       # Segundos entre simulaciones
PROB_ALERTA_SIMULADA=0.03   # 3% de probabilidad de alerta por lectura
```

### Configuración alternativa: PostgreSQL Local

Si prefieres ejecutar PostgreSQL localmente:

```env
DATABASE_URL=postgresql://postgres:1234@localhost:5432/agrostream_sq
```

Crear la base de datos:
```powershell
psql -U postgres -d postgres -c "CREATE DATABASE agrostream_sq;"
```

## 🚀 Instalación y Ejecución

### Backend (Python 3.11+)

```powershell
# 1. Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias (incluyen tabulate para benchmarks)
pip install -r requirements.txt

# 3. Asegurar conexión a PostgreSQL
python -c "from models.base import Base, engine; Base.metadata.create_all(bind=engine); from services.finca_service import FincaService; FincaService().inicializar_datos_seed(); print('✓ Base de datos lista')"

# 4. Iniciar servidor
python main.py
```

**Salida esperada:**
```
>>> Cargando .env desde: ...
✓ PostgreSQL conectado (Neon)
✓ Redis conectado (localhost:6379)    [o ⚠️ Redis no disponible (degraded mode)]
✓ Tablas creadas en PostgreSQL
✓ Datos semilla cargados
✓ SimulationManager iniciado
🚀 Servidor WebSocket escuchando en ws://localhost:5001
```

### Frontend (Node.js 18+)

En una **segunda terminal**:

```powershell
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` en el navegador.

## 📈 Benchmark Automático

Script CLI que ejecuta la simulación, recolecta métricas y genera un informe Markdown.

### Uso Básico

```powershell
# Recolectar durante 60 segundos (default)
python scripts/run_benchmark.py

# Recolectar durante 120 segundos con archivo personalizado
python scripts/run_benchmark.py --duration 120 --output mi_reporte.md

# Solo PostgreSQL
python scripts/run_benchmark.py --duration 30 --postgres-only

# Solo Redis
python scripts/run_benchmark.py --duration 30 --redis-only
```

### Parámetros CLI

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `--duration` | int | 60 | Segundos de recolección de métricas |
| `--output` | str | `benchmark_report.md` | Ruta del archivo Markdown de salida |
| `--postgres-only` | flag | false | Incluir solo operaciones PostgreSQL |
| `--redis-only` | flag | false | Incluir solo operaciones Redis |

### Ejemplo de Ejecución

```powershell
# Terminal 1: Iniciar backend
python main.py

# Terminal 2 (esperar 5 segundos a que inicie el backend)
python scripts/run_benchmark.py --duration 60 --output benchmark_result.md
```

**Salida esperada:**
```
============================================================
  🚀 AgroStream Benchmark Runner
============================================================

🔍 Verificando conectividad con PostgreSQL...
✓ PostgreSQL conectado

⏱️  Recolectando métricas durante 60 segundos...
   Inicio: 2026-05-26T12:30:45.123456Z

   [espera 60 segundos...]

✓ Período de recolección terminado
   Fin: 2026-05-26T12:31:45.123456Z

📊 Recolectando estadísticas...
   Operaciones encontradas: INSERT_lectura_postgres, HSET_sensor_estado, LPUSH_historial, ...

📝 Generando reporte en benchmark_result.md...
   ✓ Reporte guardado: benchmark_result.md

✓ ¡Benchmark completado exitosamente!

============================================================
```

### Ejemplo de Reporte Generado

**benchmark_report.md** (fragmento):

```markdown
# Informe de Benchmark: PostgreSQL vs Redis

**Generado**: 2026-05-26T12:31:50.234567Z
**Período**: 2026-05-26T12:30:45.123456Z → 2026-05-26T12:31:45.123456Z
**Duración**: 60.1 segundos

## 📊 Resumen de Volumen

- **Total de lecturas insertadas**: 12,342
- **Total de alertas generadas**: 371
- **Métricas registradas en período**: 8,945

## 📈 Estadísticas Comparativas

### PostgreSQL Operations

| Operación | Muestras | Promedio (ms) | Mediana (ms) | Mín (ms) | Máx (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|---------------|--------------|----------|----------|----------|----------|
| INSERT_lectura_postgres | 4,200 | 264.180 | 262.340 | 198.234 | 445.123 | 298.456 | 384.567 |

### Redis Operations

| Operación | Muestras | Promedio (ms) | Mediana (ms) | Mín (ms) | Máx (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|---------------|--------------|----------|----------|----------|----------|
| HSET_sensor_estado | 4,200 | 0.789 | 0.745 | 0.123 | 5.234 | 1.234 | 2.456 |
| LPUSH_historial | 4,200 | 0.523 | 0.512 | 0.087 | 3.456 | 0.987 | 1.234 |

### 🏆 Comparativa de Rendimiento

| Métrica | Valor |
|---------|-------|
| Promedio PostgreSQL | 264.180 ms |
| Promedio Redis | 0.656 ms |
| **Ratio de mejora** | **402.8x más rápido** |
| **Mejora porcentual** | **99.75%** |
```

## 🔗 Eventos WebSocket

### Evento: `benchmark_update` (Nuevo en T5/T6)

Emitido cada vez que se completa una operación (PostgreSQL o Redis).

**Estructura:**
```json
{
  "db": "postgresql",
  "operacion": "INSERT_lectura_postgres",
  "duracion_ms": 264.18,
  "timestamp": "2026-05-26T12:30:45.123456Z",
  "finca_id": "finca-001",
  "sensor_id": "sensor-temp-001"
}
```

**O para Redis:**
```json
{
  "db": "redis",
  "operacion": "HSET_sensor_estado",
  "duracion_ms": 0.789,
  "timestamp": "2026-05-26T12:30:45.124567Z",
  "finca_id": "finca-001",
  "sensor_id": "sensor-temp-001"
}
```

**Campos:**
- `db`: "postgresql" | "redis" — Identifica la base de datos de origen
- `operacion`: Nombre de la operación medida
- `duracion_ms`: Duración en milisegundos (precisión: 3 decimales)
- `timestamp`: ISO 8601 UTC
- `finca_id`: Identificador de la finca (opcional para Redis)
- `sensor_id`: Identificador del sensor (opcional para Redis)

### Evento: `simulation_benchmark`

Emitido al final de cada ciclo de simulación. Contiene estadísticas agregadas.

**Estructura:**
```json
{
  "ciclo": 5,
  "lecturas_ciclo": 9,
  "insert_ms": 264.18,
  "select_ultima_ms": 45.23,
  "filas_lecturas": 45,
  "redis_summary": {
    "HSET_sensor_estado": {
      "count": 3,
      "promedio_ms": 0.789,
      "min_ms": 0.123,
      "max_ms": 5.234
    },
    "LPUSH_historial": {
      "count": 3,
      "promedio_ms": 0.523,
      "min_ms": 0.087,
      "max_ms": 3.456
    }
  },
  "redis_errors": null
}
```

**Documentación completa:** Ver [API_WEBSOCKET.md](docs/API_WEBSOCKET.md)

## 🧪 Pruebas

### Verificar conexión PostgreSQL
```powershell
python -c "from models.base import Base, engine; Base.metadata.create_all(bind=engine); print('✓ PostgreSQL conectado')"
```

### Verificar endpoints REST
```powershell
# Fincas
curl http://localhost:5001/api/fincas/ | ConvertFrom-Json | ft

# Filas de lecturas
curl http://localhost:5001/api/benchmark/filas | ConvertFrom-Json | ft

# Estadísticas de benchmark
curl http://localhost:5001/api/benchmark/comparacion | ConvertFrom-Json | ft
```

### Verificar WebSocket (DevTools del navegador)
1. Abre `http://localhost:5173`
2. Presiona F12 → Console
3. Deberías ver conexión WebSocket con eventos en tiempo real

## 📁 Estructura del Proyecto

```
AgroStream_sql/
├── main.py                 → Punto de entrada del servidor
├── config.py              → Configuración y variables de entorno
├── requirements.txt       → Dependencias Python
├── README.md             → Este archivo
│
├── scripts/
│   └── run_benchmark.py   → ✨ NUEVO: Script CLI de benchmarks
│
├── api/                   → Rutas y endpoints Flask
│   ├── app_factory.py    → Factory de aplicación Flask
│   ├── realtime.py       → Manejadores WebSocket
│   └── routes/
│       ├── benchmark.py   → Endpoints de benchmarks
│       └── fincas.py     → Endpoints de fincas
│
├── models/                → Modelos de datos (SQLAlchemy)
│   ├── base.py           → Configuración de BD y engine
│   ├── finca.py          → Finca agrícola
│   ├── sensor.py         → Sensor de medición
│   ├── lectura.py        → Lectura de sensor
│   ├── metrica_benchmark.py → Tabla de auditoría de tiempos
│   └── alerta.py         → Alerta de umbral
│
├── services/              → Lógica de negocio
│   ├── benchmark_service.py    → Medición y cálculo de estadísticas
│   ├── ingesta_service.py      → Ingesta híbrida PostgreSQL + Redis
│   ├── alert_engine.py         → Motor de alertas
│   ├── finca_service.py        → Servicios de finca
│   └── openmeteo_client.py     → Integración con Open-Meteo
│
├── repositories/          → Acceso a base de datos
│   ├── finca_repository.py
│   ├── lectura_repository.py
│   └── alerta_repository.py
│
├── simulation/            → Simulador de sensores
│   ├── sensor_virtual.py       → Generador de lecturas virtuales
│   └── simulation_manager.py   → Orquestador de simulación
│
├── cache/                 → Cache JSON local de API externas
│   └── openmeteo/
│
└── frontend/              → React + TypeScript
    ├── src/
    │   ├── lib/           → Utilidades (tipos, Socket.IO, API HTTP)
    │   │   ├── types.ts   → Interfaces TypeScript compartidas
    │   │   ├── socket.ts  → Cliente Socket.IO
    │   │   └── api.ts     → Cliente HTTP
    │   ├── components/    → Componentes React
    │   │   ├── BenchmarkPanel.tsx  → Panel comparativo PostgreSQL vs Redis
    │   │   ├── FarmList.tsx
    │   │   ├── FarmDetail.tsx
    │   │   ├── SensorChart.tsx
    │   │   └── AlertPanel.tsx
    │   ├── App.tsx
    │   ├── main.tsx
    │   └── index.css      → Estilos Tailwind
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.json
```

## 🐛 Solución de Problemas

### El benchmark script no encuentra módulos
```powershell
# Asegúrate de estar en el venv
.\venv\Scripts\activate

# Reinstala dependencias
pip install -r requirements.txt
```

### Redis no disponible (pero la simulación continúa)
```
⚠️ Redis no disponible (degraded mode)
```

Esto es **normal y esperado**. El sistema está diseñado para funcionar sin Redis:
- PostgreSQL continúa siendo medido y registrado
- Las operaciones Redis no se ejecutan, pero los eventos WebSocket siguen llegando
- El frontend mostrará solo la serie PostgreSQL

Para habilitar Redis:
1. Asegúrate de que Redis está corriendo: `redis-cli ping` → `PONG`
2. Verifica que `REDIS_HOST` y `REDIS_PORT` en `.env` son correctos

### El frontend no recibe eventos WebSocket
1. Abre DevTools (F12) → Network → WS
2. Verifica que la conexión WebSocket esté activa
3. Verifica que el backend está en `http://localhost:5001`

### PostgreSQL no conecta
- Verifica `DATABASE_URL` en `.env`
- Para Neon: verifica conexión a Internet
- Para local: `psql -U postgres -d agrostream_sq -c "SELECT 1"`

## 📚 Documentación Adicional

- **Arquitectura Híbrida**: [trazabilidad_T5.md](trazabilidad_T5.md)
- **Frontend en Tiempo Real**: [trazabilidad_T6.md](trazabilidad_T6.md)
- **Benchmark Automático**: [trazabilidad_T7.md](trazabilidad_T7.md)
- **API WebSocket**: Documentar en [docs/API_WEBSOCKET.md](docs/API_WEBSOCKET.md) (próximamente)

## 📝 Notas Técnicas

- **Precisión de mediciones**: `time.perf_counter()` → microsegundos
- **Almacenamiento de métricas**: Tabla `metricas_benchmark` en PostgreSQL
- **Percentiles**: Calculados con interpolación (95º y 99º percentiles)
- **Ventana de gráficos**: 50 puntos máximo (sliding window para performance)
- **Graceful degradation**: Redis es opcional; el sistema funciona sin él

---

**Versión**: 2.0 (Arquitectura Híbrida con Benchmarking)  
**Última actualización**: 26 de mayo de 2026  
**Autor**: AgroStream Analytics Team


