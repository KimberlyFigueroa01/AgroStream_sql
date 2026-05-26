# PROMPT — AgroStream-SQL
## Sistema de Monitoreo Agrícola IoT (versión PostgreSQL)
### Para demostrar las diferencias de rendimiento frente a Redis

---

## CONTEXTO DEL PROYECTO

Estamos construyendo **AgroStream-SQL**, la versión relacional de un sistema de monitoreo agrícola IoT llamado AgroStream. El sistema original usa **Redis** como base de datos en memoria; esta versión usa **PostgreSQL** con el propósito explícito de **demostrar en tiempo real las diferencias de latencia y rendimiento** entre ambos enfoques.

AgroStream-SQL **no es un sistema de producción**: es una herramienta de demostración académica que simula sensores agrícolas, persiste datos en PostgreSQL y muestra métricas de latencia en tiempo real para que el usuario pueda comparar visualmente cuánto más lento es el modelo relacional frente a Redis bajo las mismas condiciones de carga.

El sistema debe verse y sentirse similar a AgroStream (el original en Redis) para que la comparación sea justa y el contraste sea evidente.

---

## STACK TECNOLÓGICO

**Backend:**
- Python 3.11+
- Flask 3.x + Flask-SocketIO 5.x (mismo stack que AgroStream original)
- SQLAlchemy 2.x como ORM (con soporte para queries raw cuando se necesite medir tiempos)
- psycopg2-binary como driver PostgreSQL
- numpy para simulación de sensores
- requests para Open-Meteo API
- python-dotenv para configuración

**Base de datos:**
- PostgreSQL 15+ (local o Railway/Supabase para demo en la nube)
- El esquema SQL completo está provisto (ver sección ESQUEMA más abajo)

**Frontend:**
- React 18 + TypeScript 5
- Vite 6
- Socket.IO Client 4
- Recharts 2 (gráficas)
- Lucide React (iconos)
- Tailwind CSS (estilos — a diferencia del original que usa CSS puro)

---

## ESTRUCTURA DE CARPETAS

```
agrostream-sql/
├── main.py                        # Punto de entrada
├── config.py                      # Configuración centralizada
├── requirements.txt
├── .env.example
├── api/
│   ├── app_factory.py             # Composition root
│   ├── routes/
│   │   ├── fincas.py              # Blueprint REST /api/fincas
│   │   └── benchmark.py           # Blueprint REST /api/benchmark ← NUEVO
│   └── realtime.py                # Eventos Socket.IO
├── models/
│   ├── base.py                    # Base declarativa SQLAlchemy
│   ├── finca.py                   # Model Finca
│   ├── sensor.py                  # Model Sensor
│   ├── lectura.py                 # Model Lectura
│   ├── alerta.py                  # Model Alerta
│   └── metrica_benchmark.py       # Model MetricaBenchmark ← NUEVO
├── repositories/
│   ├── finca_repository.py        # CRUD fincas con SQLAlchemy
│   ├── lectura_repository.py      # Ingesta y consultas de lecturas
│   └── alerta_repository.py       # Gestión de alertas
├── services/
│   ├── finca_service.py           # Lógica de negocio
│   ├── ingesta_service.py         # Validación + persistencia + benchmark
│   ├── alert_engine.py            # Umbrales críticos
│   ├── benchmark_service.py       # Medición y comparación ← NUEVO
│   └── openmeteo_client.py        # API Open-Meteo + caché JSON
├── simulation/
│   ├── simulation_manager.py      # Hilo daemon de simulación
│   └── sensor_virtual.py          # Generador de lecturas con ruido gaussiano
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── App.tsx
│   │   ├── lib/
│   │   │   ├── api.ts             # Cliente REST
│   │   │   ├── socket.ts          # Singleton Socket.IO
│   │   │   └── types.ts           # Tipos compartidos
│   │   └── components/
│   │       ├── FarmList.tsx
│   │       ├── FarmDetail.tsx
│   │       ├── MetricCard.tsx
│   │       ├── SensorChart.tsx
│   │       ├── AlertPanel.tsx
│   │       └── BenchmarkPanel.tsx  ← NUEVO (panel de comparación)
└── cache/                          # Caché JSON de Open-Meteo (igual que original)
```

---

## ESQUEMA DE BASE DE DATOS

Usar exactamente este esquema SQL para crear las tablas en PostgreSQL:

```sql
-- Tabla: fincas
CREATE TABLE fincas (
    id              VARCHAR(64)     PRIMARY KEY,
    nombre          VARCHAR(120)    NOT NULL,
    lat             DECIMAL(9,6)    NOT NULL,
    lon             DECIMAL(9,6)    NOT NULL,
    altitud_m       INTEGER         NOT NULL DEFAULT 0,
    ciudad          VARCHAR(100),
    departamento    VARCHAR(100),
    activa          BOOLEAN         NOT NULL DEFAULT TRUE,
    creada_en       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    actualizada_en  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Tabla: sensores
CREATE TABLE sensores (
    id              VARCHAR(128)    PRIMARY KEY,
    finca_id        VARCHAR(64)     NOT NULL REFERENCES fincas(id) ON DELETE CASCADE,
    tipo            VARCHAR(40)     NOT NULL,
    unidad          VARCHAR(20)     NOT NULL,
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sensores_finca ON sensores(finca_id);

-- Tabla: lecturas  ← la que demuestra el cuello de botella
CREATE TABLE lecturas (
    id              BIGSERIAL       PRIMARY KEY,
    sensor_id       VARCHAR(128)    NOT NULL REFERENCES sensores(id) ON DELETE CASCADE,
    finca_id        VARCHAR(64)     NOT NULL REFERENCES fincas(id)   ON DELETE CASCADE,
    tipo            VARCHAR(40)     NOT NULL,
    valor           DECIMAL(10,4)   NOT NULL,
    unidad          VARCHAR(20)     NOT NULL,
    fuente          VARCHAR(20)     NOT NULL DEFAULT 'openmeteo',
    anomalia        BOOLEAN         NOT NULL DEFAULT FALSE,
    lat             DECIMAL(9,6),
    lon             DECIMAL(9,6),
    altitud_m       INTEGER,
    timestamp       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_lecturas_sensor_ts ON lecturas(sensor_id, timestamp DESC);
CREATE INDEX idx_lecturas_finca_ts  ON lecturas(finca_id,  timestamp DESC);
CREATE INDEX idx_lecturas_tipo_ts   ON lecturas(tipo,       timestamp DESC);
CREATE INDEX idx_lecturas_timestamp ON lecturas(timestamp DESC);

-- Tabla: alertas
CREATE TABLE alertas (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    sensor_id       VARCHAR(128)    NOT NULL REFERENCES sensores(id) ON DELETE CASCADE,
    finca_id        VARCHAR(64)     NOT NULL REFERENCES fincas(id)   ON DELETE CASCADE,
    finca_nombre    VARCHAR(120)    NOT NULL,
    tipo_sensor     VARCHAR(40)     NOT NULL,
    nivel           VARCHAR(20)     NOT NULL CHECK (nivel IN ('critico','advertencia','info')),
    mensaje         TEXT            NOT NULL,
    valor           DECIMAL(10,4)   NOT NULL,
    unidad          VARCHAR(20)     NOT NULL,
    umbral_min      DECIMAL(10,4),
    umbral_max      DECIMAL(10,4),
    timestamp       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    leida           BOOLEAN         NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_alertas_finca_ts  ON alertas(finca_id,  timestamp DESC);
CREATE INDEX idx_alertas_global_ts ON alertas(timestamp DESC);

-- Tabla: metricas_benchmark  ← corazón de la demo
CREATE TABLE metricas_benchmark (
    id              BIGSERIAL       PRIMARY KEY,
    operacion       VARCHAR(60)     NOT NULL,
    duracion_ms     DECIMAL(10,3)   NOT NULL,
    filas_tabla     BIGINT          NOT NULL DEFAULT 0,
    timestamp       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_bench_op ON metricas_benchmark(operacion, timestamp DESC);
```

---

## MÓDULO DE BENCHMARK — ESPECIFICACIÓN DETALLADA

Este es el componente central de la demo. Debe implementarse con máxima precisión.

### benchmark_service.py

```python
import time
from decimal import Decimal

class BenchmarkService:
    """
    Mide el tiempo real de cada operación SQL y lo guarda en metricas_benchmark.
    El frontend lee estas métricas por WebSocket para mostrarlas en tiempo real.
    """

    def medir_insert_lectura(self, lectura_data: dict) -> dict:
        """
        Mide el tiempo de INSERT en lecturas (incluyendo actualización de índices).
        Retorna: { duracion_ms, filas_tabla, operacion }
        """
        pass  # implementar

    def medir_select_ultima_finca(self, finca_id: str) -> dict:
        """
        Mide el tiempo del SELECT con JOIN para obtener última lectura por finca.
        Query a medir:
            SELECT DISTINCT ON (l.tipo) l.tipo, l.valor, l.unidad, l.timestamp
            FROM lecturas l
            JOIN sensores s ON s.id = l.sensor_id
            WHERE s.finca_id = %s
            ORDER BY l.tipo, l.timestamp DESC
        Retorna: { duracion_ms, filas_tabla, operacion, resultado }
        """
        pass  # implementar

    def medir_select_historial(self, sensor_id: str, limite: int = 60) -> dict:
        """
        Mide el tiempo de SELECT para el historial de un sensor.
        Query a medir:
            SELECT valor, timestamp FROM lecturas
            WHERE sensor_id = %s
            ORDER BY timestamp DESC LIMIT %s
        Retorna: { duracion_ms, filas_tabla, operacion, resultado }
        """
        pass  # implementar

    def obtener_estadisticas(self, operacion: str = None, ultimas_n: int = 100) -> dict:
        """
        Retorna estadísticas agregadas de las métricas registradas:
        { promedio_ms, mediana_ms, max_ms, min_ms, total_operaciones, filas_actuales }
        Si operacion es None, retorna stats de todas las operaciones.
        """
        pass  # implementar

    def obtener_comparacion_redis(self) -> dict:
        """
        Retorna un dict con los tiempos típicos de Redis para las mismas operaciones,
        tomados de la documentación oficial de Redis (constantes, no medidas reales).
        Se usa para mostrar la comparación en el panel.
        Valores de referencia:
            INSERT (HSET+LPUSH+LTRIM): < 1 ms
            SELECT última finca (HGETALL): < 1 ms
            SELECT historial (LRANGE): < 1 ms
        """
        return {
            "INSERT_lectura":        { "referencia_ms": 0.5,  "descripcion": "HSET + LPUSH + LTRIM" },
            "SELECT_ultima_finca":   { "referencia_ms": 0.3,  "descripcion": "HGETALL finca:{id}:ultima" },
            "SELECT_historial":      { "referencia_ms": 0.4,  "descripcion": "LRANGE sensor:{id}:stream 0 59" },
        }
```

### API REST — /api/benchmark

```
GET  /api/benchmark/stats              → estadísticas agregadas por operación
GET  /api/benchmark/comparacion        → tiempos SQL vs Redis (para el panel)
GET  /api/benchmark/historial?op=X&n=Y → últimas N métricas de operación X
POST /api/benchmark/reset              → borra metricas_benchmark (reiniciar demo)
GET  /api/benchmark/filas              → número actual de filas en tabla lecturas
```

### Eventos WebSocket nuevos

```
# Servidor → cliente (emitir cada vez que se registra una métrica)
benchmark_update  →  { operacion, duracion_ms, filas_tabla, timestamp, comparacion_redis }

# Emitir también en cada ciclo de simulación
simulation_benchmark  →  {
    insert_ms:          float,   # tiempo del INSERT de esta lectura
    select_ultima_ms:   float,   # tiempo del SELECT de estado actual
    filas_lecturas:     int,     # tamaño actual de la tabla
    timestamp:          str
}
```

---

## SIMULACIÓN DE SENSORES

La simulación debe ser **idéntica** a la de AgroStream original para que la comparación sea justa:

- **Intervalo:** 5 segundos por defecto (configurable en config.py)
- **Sensores por finca:** 9 (temperatura×2, humedad×2, co2×1, humedad_suelo×3, radiacion×1)
- **Generación de lectura:** base Open-Meteo + ruido gaussiano (numpy) + deriva lenta + anomalías 0.5%
- **Fincas iniciales:** mismas 3 fincas en Boyacá/Cundinamarca del esquema SQL
- **Open-Meteo:** misma integración con caché en disco (cache/openmeteo/ TTL 1h, fallback físico local)
- **AlertEngine:** mismos umbrales:
  - temperatura: < 2°C (helada) | > 35°C (estrés térmico)
  - humedad: < 30% | > 90%
  - co2: > 1000 ppm
  - humedad_suelo: < 20% | > 80%

**Diferencia clave en la simulación:** cada ciclo debe llamar a `BenchmarkService.medir_insert_lectura()` y emitir el tiempo medido por WebSocket. Esto permite que el usuario vea en tiempo real cuánto tarda cada INSERT a medida que la tabla crece.

---

## FRONTEND — COMPONENTE BenchmarkPanel

Este es el componente más importante de la interfaz. Debe mostrar:

### Sección 1: Comparación en tiempo real
```
┌─────────────────────────────────────────────────────────────┐
│  RENDIMIENTO EN TIEMPO REAL              [Filas: 12,450]    │
├─────────────────────────────────────────────────────────────┤
│                    PostgreSQL (SQL)        Redis (referencia)│
│  INSERT lectura    ████████ 12.3 ms       ▌ 0.5 ms         │
│  Leer estado finca ████████████ 45.2 ms   ▌ 0.3 ms         │
│  Historial sensor  ████ 8.1 ms            ▌ 0.4 ms         │
└─────────────────────────────────────────────────────────────┘
```
- Barras comparativas con color verde (Redis) y naranja/rojo (SQL)
- El ancho de la barra SQL crece visualmente a medida que la tabla acumula filas
- Actualización en tiempo real via Socket.IO (evento `benchmark_update`)

### Sección 2: Gráfica de tendencia de latencia
- Gráfica de línea (Recharts LineChart) con el tiempo de INSERT en el eje Y y el número de filas en el eje X
- Muestra cómo la latencia crece a medida que la tabla se llena
- Línea de referencia horizontal en 1ms (nivel Redis)
- Actualización automática cada vez que llega `simulation_benchmark`

### Sección 3: Estadísticas acumuladas
```
┌──────────────────────────────────────────┐
│  Operación: INSERT_lectura               │
│  Promedio: 11.2 ms  │  Máximo: 28.4 ms  │
│  Mínimo:    3.1 ms  │  Total ops: 1,247  │
└──────────────────────────────────────────┘
```

### Sección 4: Explicación contextual (texto dinámico)
Mostrar un texto que cambie según el número de filas actual:
- 0–10k filas: "La tabla aún es pequeña. El rendimiento de SQL es aceptable."
- 10k–100k filas: "Con más datos, SQL empieza a mostrar su limitación: cada INSERT actualiza múltiples índices."
- 100k+ filas: "Con más de 100.000 filas, la diferencia es clara. Redis mantiene < 1ms sin importar el volumen."

---

## CONFIGURACIÓN (config.py)

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/agrostream_sql")

# Simulación — mismos valores que AgroStream original
INTERVALO_LECTURA_S   = int(os.getenv("INTERVALO_LECTURA_S", 5))
PROB_ALERTA_SIMULADA  = float(os.getenv("PROB_ALERTA_SIMULADA", 0.03))

SENSORES_POR_FINCA = {
    "temperatura":   2,
    "humedad":       2,
    "co2":           1,
    "humedad_suelo": 3,
    "radiacion":     1,
}

# Umbrales de alerta — Altiplano Cundiboyacense
UMBRALES = {
    "temperatura":   { "min": 2.0,  "max": 35.0 },
    "humedad":       { "min": 30.0, "max": 90.0 },
    "co2":           { "min": None, "max": 1000.0 },
    "humedad_suelo": { "min": 20.0, "max": 80.0 },
    "radiacion":     { "min": None, "max": None },
}

# Open-Meteo
OPENMETEO_FORECAST_URL  = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/reverse"
CACHE_DIR_OPENMETEO     = "cache/openmeteo"
CACHE_DIR_GEOCODING     = "cache/geocoding"
CACHE_TTL_OPENMETEO_S   = 3600    # 1 hora
CACHE_TTL_GEOCODING_S   = 86400   # 24 horas

# Flask
FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))  # 5001 para no chocar con AgroStream (5000)
FLASK_HOST = "0.0.0.0"

# Fincas iniciales — mismas que AgroStream
FINCAS = [
    { "id": "finca_001", "nombre": "Finca El Roble",      "lat": 5.5353, "lon": -73.3621, "altitud_m": 2650 },
    { "id": "finca_002", "nombre": "Finca La Esperanza",  "lat": 4.8833, "lon": -74.0000, "altitud_m": 2600 },
    { "id": "finca_003", "nombre": "Finca Los Alisos",    "lat": 5.7011, "lon": -72.9281, "altitud_m": 2500 },
]
```

---

## DIFERENCIAS EXPLÍCITAS CON AGROSTREAM ORIGINAL

Estas diferencias deben estar presentes en el código y visibles en la interfaz:

| Aspecto | AgroStream (Redis) | AgroStream-SQL (esta app) |
|---|---|---|
| Base de datos | Redis (memoria RAM) | PostgreSQL (disco) |
| Escritura | HSET + LPUSH + LTRIM, O(1) | INSERT + 4 índices, O(log n) |
| Lectura estado finca | HGETALL (1 op de red) | SELECT + JOIN 2 tablas |
| Historial sensor | LRANGE 0 59 | SELECT + ORDER BY + LIMIT |
| Limpieza automática | TTL nativo de Redis | JOB manual con DELETE |
| Puerto | 5000 | 5001 |
| Panel benchmark | No existe | Panel central de la demo |

---

## REQUISITOS DE IMPLEMENTACIÓN

1. **El benchmark debe medirse con `time.perf_counter()`**, no con `time.time()`, para mayor precisión en rangos de milisegundos.

2. **Las queries críticas deben ejecutarse con SQL raw** (no ORM) cuando se mide el tiempo, para evitar que el overhead de SQLAlchemy distorsione la medición. Usar `connection.execute(text(...))` con `time.perf_counter()` antes y después.

3. **El SimulationManager debe medir Y emitir** el tiempo de cada INSERT vía WebSocket en cada ciclo, para que el panel de benchmark se actualice en tiempo real sin que el usuario tenga que hacer nada.

4. **La tabla `metricas_benchmark` no debe tener TTL**: acumula todas las mediciones de la sesión para que la gráfica de tendencia muestre la degradación progresiva a medida que `lecturas` crece.

5. **La interfaz debe tener dos modos de vista**:
   - Vista normal (igual a AgroStream): listado de fincas, lecturas en tiempo real, alertas
   - Vista benchmark (tab separado): panel completo de comparación SQL vs Redis

6. **El frontend debe conectarse al mismo WebSocket** y diferenciar los eventos normales (`sensor_reading`, `sensor_alerts`) de los de benchmark (`benchmark_update`, `simulation_benchmark`).

7. **Incluir un botón "Acelerar simulación"** que baje el intervalo de 5s a 1s para poblar la tabla más rápido y hacer visible la degradación en menos tiempo durante la demo.

8. **Incluir un botón "Resetear benchmark"** que llame a `POST /api/benchmark/reset` y limpie `metricas_benchmark` (pero NO `lecturas`, para no perder el volumen acumulado).

---

## INSTRUCCIONES DE ARRANQUE (README)

El README debe incluir:

```bash
# 1. Clonar y entrar al proyecto
git clone <repo>
cd agrostream-sql

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con la URL de tu instancia PostgreSQL

# 4. Crear tablas e insertar datos iniciales
python -c "from api.app_factory import create_app; app = create_app(); print('BD lista')"

# 5. Iniciar backend
python main.py

# 6. En otra terminal — iniciar frontend
cd frontend
npm install
npm run dev

# Acceder a http://localhost:5173
# El backend corre en http://localhost:5001
```

---

## OBJETIVO ACADÉMICO (incluir como comentario en App.tsx)

```
AgroStream-SQL demuestra empíricamente por qué las bases de datos relacionales
no son la herramienta adecuada para sistemas IoT de alta frecuencia.
No se trata de que SQL sea malo: es la herramienta incorrecta para este patrón
de carga específico. AgroStream (Redis) resuelve el mismo problema con latencia
constante < 1ms independientemente del volumen de datos acumulado.
```
