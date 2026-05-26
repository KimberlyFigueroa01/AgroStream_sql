# AgroStream-SQL — Análisis Técnico Completo

## 1. Árbol de Archivos

```
config.py                           # Variables de entorno y constantes globales
main.py                             # Punto de entrada, Flask + SocketIO
requirements.txt                    # Dependencias Python (Flask, SQLAlchemy)
README.md                           # Documentación general
prompt_agrostream_sql.md            # Prompt del sistema

api/
  __init__.py                       # Marcador de paquete
  app_factory.py                    # Composición root, crea app y registra blueprints
  realtime.py                       # Eventos SocketIO (connect, disconnect, request handlers)
  routes/
    __init__.py                     # Marcador de paquete
    fincas.py                       # Endpoints REST para fincas, lecturas, alertas
    benchmark.py                    # Endpoints REST para benchmark SQL vs Redis

models/
  __init__.py                       # Marcador de paquete
  base.py                           # Base declarativa SQLAlchemy, engine, session
  finca.py                          # Modelo ORM tabla fincas (ubicación, altitud)
  sensor.py                         # Modelo ORM tabla sensores (tipo, unidad)
  lectura.py                        # Modelo ORM tabla lecturas (serie temporal medida)
  alerta.py                         # Modelo ORM tabla alertas (umbral violado)
  metrica_benchmark.py              # Modelo ORM tabla metricas_benchmark (tiempos)

repositories/
  __init__.py                       # Marcador de paquete
  finca_repository.py               # Consultas persistencia fincas, sensores
  lectura_repository.py             # Consultas lecturas historial por sensor
  alerta_repository.py              # Consultas crear, listar alertas de finca

services/
  __init__.py                       # Marcador de paquete
  finca_service.py                  # Lógica fincas, seed inicial datos
  ingesta_service.py                # Validación + persistencia lecturas + benchmark
  alert_engine.py                   # Motor evaluación umbrales alertas críticas
  benchmark_service.py              # Mide tiempos INSERT/SELECT con perf_counter
  openmeteo_client.py               # Cliente HTTP a API Open-Meteo externa

simulation/
  __init__.py                       # Marcador de paquete
  sensor_virtual.py                 # Generador datos simulados sensores IoT
  simulation_manager.py             # Hilo daemon ciclos simulación, emite WebSocket

cache/
  openmeteo/                        # Cache JSON respuestas Open-Meteo (1 hora TTL)

frontend/
  package.json                      # Scripts npm, dependencias (React, Socket.io)
  tsconfig.json                     # Configuración TypeScript
  tsconfig.node.json                # Configuración TypeScript para Vite
  vite.config.ts                    # Bundler Vite, puerto 5173
  tailwind.config.js                # Framework CSS utility-first Tailwind
  postcss.config.js                 # Procesador CSS compatible Tailwind
  index.html                        # Entry point HTML, mount React
  src/
    main.tsx                        # Boot React, renderiza App en DOM
    App.tsx                         # Componente raíz, layout principal
    index.css                       # Estilos globales CSS + Tailwind
    components/
      FarmList.tsx                  # Lista clickeable fincas seleccionables
      FarmDetail.tsx                # Panel detalles finca, mapa, sensores
      SensorChart.tsx               # Gráfico Recharts series temporal sensor
      MetricCard.tsx                # Tarjeta métrica (temperatura, humedad actual)
      BenchmarkPanel.tsx            # Panel comparación SQL vs Redis tiempos
      AlertPanel.tsx                # Panel alertas críticas filtradas por finca
    lib/
      api.ts                        # Funciones fetch REST (getFincas, getLecturas)
      socket.ts                     # Cliente Socket.io singleton conexión backend
      types.ts                      # Interfaces TypeScript Finca, Lectura, Alerta
```

## 2. Tecnologías

### Backend
- **Lenguaje**: Python 3.9+
- **Framework Web**: Flask 3.0.3
- **WebSocket**: Flask-SocketIO 5.5.1 (threading async_mode)
- **ORM/SQL**: SQLAlchemy 2.0.41
- **Base Datos**: PostgreSQL (Neon Cloud)
- **Driver**: psycopg2-binary 2.9.3
- **HTTP Client**: requests 2.32.3
- **Config**: python-dotenv 1.0.1
- **Math**: numpy 1.24.4

### Frontend
- **Lenguaje**: TypeScript 5.7.3
- **Framework UI**: React 18.3.1
- **Bundler**: Vite 6.0.7
- **CSS**: Tailwind 3.4.17 + PostCSS
- **Gráficos**: Recharts 2.15.3
- **Iconos**: Lucide React 0.469.0
- **WebSocket**: Socket.io-client 4.8.1
- **Tipado**: @types/react 18.3.18

### Infraestructura
- **BD**: PostgreSQL (Neon)
- **Puerto Backend**: 5001
- **Puerto Frontend**: 5173 (Vite dev)
- **CORS**: Habilitado localhost:5173, 5174

## 3. Flujo de Datos: Simulación → Frontend

- **Inicio**: `main.py` → `app_factory.py` crea Flask + SocketIO
- **Seed BD**: `FincaService.inicializar_datos_seed()` inserta 3 fincas + 9 sensores
- **Loop Simulación**: `SimulationManager._loop()` cada 5s (configurable)
  - Obtiene todas fincas: `FincaRepository.obtener_todas()`
  - Por cada finca × sensor:
    - `SensorVirtual.generar_lectura()` → datos simulados
    - `IngestaService.ingestar_lectura()` → mide INSERT + evalúa alertas
    - `BenchmarkService.medir_insert_lectura()` → tiempo perf_counter + registra en tabla
    - Emite WebSocket `sensor_reading` → Frontend recibe lectura
    - `AlertEngine.evaluar()` → si viola umbral, emite `sensor_alerts`
  - Final ciclo: emite `simulation_benchmark` resumen (INSERT avg, SELECT avg, filas)
- **Frontend**: React escucha eventos WebSocket, actualiza gráficos/tarjetas
- **Persistencia**: Todas las métricas se guardan en `metricas_benchmark` tabla

## 4. Endpoints REST

### Fincas

| Método | Ruta | Descripción | Body |
|--------|------|-------------|------|
| GET | `/api/fincas/` | Lista todas las fincas activas | - |
| GET | `/api/fincas/<finca_id>` | Detalle una finca (id, nombre, lat, lon, altitud) | - |
| GET | `/api/fincas/<finca_id>/sensores` | Sensores de una finca (tipo, unidad, estado) | - |
| GET | `/api/fincas/<finca_id>/lecturas` | Última lectura por tipo de sensor | - |
| GET | `/api/fincas/<finca_id>/historial/<sensor_id>` | Historial 60 últimas lecturas sensor (query: `?limite=N`) | - |
| GET | `/api/fincas/<finca_id>/alertas` | Alertas finca (query: `?limite=50`) | - |

### Alertas Globales

| Método | Ruta | Descripción | Body |
|--------|------|-------------|------|
| GET | `/api/fincas/alertas/globales` | Todas las alertas recientes (query: `?limite=100`) | - |
| GET | `/api/fincas/alertas/no-leidas` | Conteo alertas sin leer | - |
| POST | `/api/fincas/alertas/<alerta_id>/leer` | Marca alerta como leída | `{}` |

### Benchmark SQL vs Redis

| Método | Ruta | Descripción | Body |
|--------|------|-------------|------|
| GET | `/api/benchmark/stats` | Estadísticas por operación (query: `?op=INSERT_lectura`) | - |
| GET | `/api/benchmark/comparacion` | Tiempos SQL real vs Redis referencia | - |
| GET | `/api/benchmark/historial` | Últimas N métricas operación (query: `?op=INSERT_lectura&n=100`) | - |
| POST | `/api/benchmark/reset` | Borra métricas (NO lecturas) | `{}` |
| GET | `/api/benchmark/filas` | Número actual filas tabla lecturas | - |

## 5. Eventos WebSocket

### Cliente → Servidor

| Evento | Dirección | Descripción | Payload Ejemplo |
|--------|-----------|-------------|-----------------|
| `connect` | ← | Cliente conecta (automático) | - |
| `request_farm_data` | → | Solicita datos última lectura + alertas | `{ "finca_id": "finca_001" }` |
| `request_sensor_history` | → | Solicita historial sensor | `{ "sensor_id": "finca_001:temperatura:0", "limite": 60 }` |
| `change_interval` | → | Cambia intervalo simulación | `{ "intervalo": 2 }` |

### Servidor → Cliente (Emitidos por SimulationManager)

| Evento | Dirección | Descripción | Payload Ejemplo |
|--------|-----------|-------------|-----------------|
| `sensor_reading` | ← | Nueva lectura sensor en tiempo real | `{ "finca_id": "finca_001", "sensor_id": "...", "tipo": "temperatura", "valor": 24.5, "unidad": "°C", "anomalia": false, "timestamp": "2026-05-26T..." }` |
| `sensor_alerts` | ← | Alertas generadas (múltiples) | `[{ "id": "...", "finca_id": "finca_001", "tipo_sensor": "temperatura", "nivel": "critico", "mensaje": "🔥 ESTRÉS TÉRMICO...", "valor": 38.2, "umbral_max": 35.0, ... }]` |
| `benchmark_update` | ← | Métrica INSERT individual (por cada lectura) | `{ "operacion": "INSERT_lectura", "duracion_ms": 1.245, "filas_tabla": 3450, "comparacion_redis": { "promedio_ms": 0.05, "max_ms": 0.15 }, "timestamp": "2026-05-26T..." }` |
| `simulation_benchmark` | ← | Resumen ciclo simulación (INSERT avg, SELECT avg) | `{ "insert_ms": 1.18, "select_ultima_ms": 5.42, "filas_lecturas": 3450, "ciclo": 128, "lecturas_ciclo": 9, "timestamp": "2026-05-26T..." }` |
| `interval_changed` | ← | Confirmación cambio intervalo | `{ "intervalo": 2 }` |

## 6. Modelos de Datos (PostgreSQL)

### Tabla `fincas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` (PK) | `VARCHAR(64)` | Identificador único (ej: "finca_001") |
| `nombre` | `VARCHAR(120)` | Nombre descriptivo |
| `lat` | `NUMERIC(9,6)` | Latitud Altiplano Cundiboyacense |
| `lon` | `NUMERIC(9,6)` | Longitud |
| `altitud_m` | `INTEGER` | Altitud metros |
| `ciudad` | `VARCHAR(100)` | Ciudad/municipio |
| `departamento` | `VARCHAR(100)` | Departamento Colombia |
| `activa` | `BOOLEAN` | Estado finca (default: true) |
| `creada_en` | `TIMESTAMP` | server_default: now() |
| `actualizada_en` | `TIMESTAMP` | Actualiza en cada cambio |

### Tabla `sensores`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` (PK) | `VARCHAR(128)` | ID único (ej: "finca_001:temperatura:0") |
| `finca_id` (FK) | `VARCHAR(64)` | Referencia finca (ondelete: CASCADE) |
| `tipo` | `VARCHAR(40)` | Tipo sensor (temperatura, humedad, co2, etc.) |
| `unidad` | `VARCHAR(20)` | Unidad (°C, %, ppm, W/m²) |
| `activo` | `BOOLEAN` | Estado sensor (default: true) |
| `creado_en` | `TIMESTAMP` | server_default: now() |
| Index | `idx_sensores_finca` | (finca_id) |

### Tabla `lecturas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` (PK) | `BIGINT` | Autoincrement, demostración escala |
| `sensor_id` (FK) | `VARCHAR(128)` | Referencia sensor (ondelete: CASCADE) |
| `finca_id` (FK) | `VARCHAR(64)` | Referencia finca (ondelete: CASCADE) |
| `tipo` | `VARCHAR(40)` | Tipo sensor (redundante, optimización) |
| `valor` | `NUMERIC(10,4)` | Valor medido |
| `unidad` | `VARCHAR(20)` | Unidad medida |
| `fuente` | `VARCHAR(20)` | Origen: "openmeteo" o "simulada" |
| `anomalia` | `BOOLEAN` | Flag detección anomalía (default: false) |
| `lat` | `NUMERIC(9,6)` | Latitude opcional (null) |
| `lon` | `NUMERIC(9,6)` | Longitude opcional (null) |
| `altitud_m` | `INTEGER` | Altitud opcional (null) |
| `timestamp` | `TIMESTAMP` | server_default: now() |
| Índices | - | idx_lecturas_sensor_ts, idx_lecturas_finca_ts, idx_lecturas_tipo_ts, idx_lecturas_timestamp DESC (para ORDER BY) |

### Tabla `alertas`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` (PK) | `UUID` | Identificador único UUID v4 |
| `sensor_id` (FK) | `VARCHAR(128)` | Referencia sensor (ondelete: CASCADE) |
| `finca_id` (FK) | `VARCHAR(64)` | Referencia finca (ondelete: CASCADE) |
| `finca_nombre` | `VARCHAR(120)` | Cache nombre para UI |
| `tipo_sensor` | `VARCHAR(40)` | Tipo sensor (redundante) |
| `nivel` | `VARCHAR(20)` | Nivel alerta: "critico", "advertencia", "info" |
| `mensaje` | `TEXT` | Mensaje descriptivo alerta |
| `valor` | `NUMERIC(10,4)` | Valor medido que violó umbral |
| `unidad` | `VARCHAR(20)` | Unidad valor |
| `umbral_min` | `NUMERIC(10,4)` | Umbral mínimo violated (nullable) |
| `umbral_max` | `NUMERIC(10,4)` | Umbral máximo violated (nullable) |
| `timestamp` | `TIMESTAMP` | server_default: now() |
| `leida` | `BOOLEAN` | Flag lectura usuario (default: false) |
| Check Constraint | - | nivel IN ('critico','advertencia','info') |
| Índices | - | idx_alertas_finca_ts, idx_alertas_global_ts |

### Tabla `metricas_benchmark`
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` (PK) | `BIGINT` | Autoincrement |
| `operacion` | `VARCHAR(60)` | Nombre operación (ej: "INSERT_lectura", "SELECT_ultima_finca") |
| `duracion_ms` | `NUMERIC(10,3)` | Tiempo ejecución milisegundos |
| `filas_tabla` | `BIGINT` | Número filas tabla lecturas en ese momento |
| `timestamp` | `TIMESTAMP` | server_default: now() |
| Índice | - | idx_bench_op (operacion, timestamp DESC) |

## 7. Servicios Principales

| Archivo | Clase/Función | Responsabilidad |
|---------|---------------|-----------------|
| `api/app_factory.py` | `create_app()` | Composición root Flask+SocketIO+Blueprints |
| `models/base.py` | `engine`, `SessionLocal` | Conexión PostgreSQL, sesión ORM |
| `repositories/finca_repository.py` | `FincaRepository` | Consultas persistencia fincas, sensores |
| `repositories/lectura_repository.py` | `LecturaRepository` | Consultas historial lecturas sensor |
| `repositories/alerta_repository.py` | `AlertaRepository` | Consultas crear, listar alertas |
| `services/finca_service.py` | `FincaService` | Lógica fincas, seed 3 fincas+9 sensores |
| `services/ingesta_service.py` | `IngestaService` | Coordinación INSERT+benchmark+alertas |
| `services/benchmark_service.py` | `BenchmarkService` | Mide tiempos INSERT/SELECT perf_counter |
| `services/alert_engine.py` | `AlertEngine` | Evaluación umbrales, genera alertas críticas |
| `services/openmeteo_client.py` | `OpenMeteoClient` | Cliente HTTP Open-Meteo forecast |
| `simulation/sensor_virtual.py` | `SensorVirtual` | Generador datos simulados (numpy random) |
| `simulation/simulation_manager.py` | `SimulationManager` | Hilo daemon ciclos, emit WebSocket |
| `api/realtime.py` | `register_events()` | Handlers SocketIO connect/disconnect/request |

## 8. Variables de Entorno (.env)

```
DATABASE_URL=postgresql://user:pass@host/db
# Conexión PostgreSQL Neon completa con SSL

INTERVALO_LECTURA_S=5
# Segundos entre ciclos simulación (default: 5, min: 1, máx: 30)

PROB_ALERTA_SIMULADA=0.03
# Probabilidad generar anomalía por lectura (default: 3%)

FLASK_PORT=5001
# Puerto servidor backend (default: 5001 para evitar conflictos)
```

## 9. Ejecución

### Backend

```bash
# Clonar repositorio
git clone <repo_url>
cd AgroStream_sql

# Crear entorno Python
python -m venv venv
.\venv\Scripts\activate          # Windows
source venv/bin/activate         # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env (copiar plantilla y llenar DATABASE_URL)
# Crear archivo .env con:
# DATABASE_URL=postgresql://...

# Ejecutar servidor backend
python main.py

# Salida esperada:
# ============================================================
#   AgroStream-SQL  —  Monitoreo Agrícola IoT (PostgreSQL)
#   Backend: http://0.0.0.0:5001
#   Intervalo de simulación: 5s
# ============================================================
#   ✓ Tablas creadas/verificadas
#   ✓ Datos seed listos
#   🌱 Simulación iniciada (intervalo: 5s)
```

### Frontend

```bash
# En terminal nueva (desde carpeta frontend/)
cd frontend

# Instalar dependencias Node
npm install

# Ejecutar servidor Vite desarrollo
npm run dev

# Salida esperada:
# VITE v6.0.7  ready in XXX ms
# ➜  Local:   http://localhost:5173/
# ➜  Press h to show help

# Abrir navegador http://localhost:5173/
```

### Compilar Producción

```bash
# Frontend
cd frontend
npm run build
# Genera carpeta dist/ lista para servir

# Backend
# No requiere compilación, ejecutar como pytest/gunicorn en producción
```
