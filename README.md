# AgroStream-SQL (PostgreSQL)

Este proyecto levanta un backend Flask + Socket.IO que simula sensores agrícolas e inserta lecturas en PostgreSQL, junto con un frontend React que consume la API y eventos en tiempo real vía WebSocket.

## Requisitos

- **Python 3.11+**
- **Node.js 18+** (para el frontend)
- **PostgreSQL 15+** (opcional, si usas una BD local. Actualmente está configurado para usar Neon)

## Base de Datos

### Ubicación actual

La base de datos está alojada en **Neon** (PostgreSQL en la nube).

**URL de conexión:**
```
postgresql://neondb_owner:npg_KAwvptrW6Q0i@ep-damp-field-aqchkfoj.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require
```

Esta URL se define en el archivo `.env`:

```env
DATABASE_URL=postgresql://neondb_owner:npg_KAwvptrW6Q0i@ep-damp-field-aqchkfoj.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require
```

### Si deseas usar PostgreSQL local

Si prefieres ejecutar la BD localmente en tu máquina:

1. Asegúrate de tener PostgreSQL instalado
2. Crea la base de datos:

```powershell
psql -U postgres -d postgres -c "CREATE DATABASE agrostream_sq;"
```

3. Edita `.env` y reemplaza la URL:

```env
DATABASE_URL=postgresql://postgres:1234@localhost:5432/agrostream_sq
```

### Inicializar el esquema

El backend crea automáticamente las tablas al arrancar. Si necesitas inicializar manualmente:

```powershell
# Con el venv activado
python -c "from models.base import Base, engine; Base.metadata.create_all(bind=engine); from services.finca_service import FincaService; FincaService().inicializar_datos_seed(); print('✓ Base de datos lista')"
```

## Instalación y ejecución

### Backend (Python + Flask + Socket.IO)

Desde la raíz del proyecto:

```powershell
# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
python main.py
```

El backend se inicia automáticamente en:
- **URL:** `http://localhost:5001`
- **WebSocket:** `ws://localhost:5001`

Al arrancar:
- ✓ Verifica/crea tablas en PostgreSQL
- ✓ Carga datos semilla (fincas, sensores, alertas)
- ✓ Inicia la simulación de sensores

### Frontend (React + TypeScript + Tailwind)

En una **segunda terminal** (mantén el backend ejecutándose):

```powershell
cd frontend
npm install
npm run dev
```

Abre en tu navegador:
- **URL:** `http://localhost:5173`

El frontend se conecta automáticamente al WebSocket del backend y recibe actualizaciones en tiempo real.

## Pruebas

### ✓ Prueba 1: Verificar conexión a base de datos

Sin levantar la aplicación completa:

```powershell
# Con el venv activado
python -c "from models.base import Base, engine; Base.metadata.create_all(bind=engine); from services.finca_service import FincaService; FincaService().inicializar_datos_seed(); print('✓ Base de datos lista')"
```

Si ves `✓ Base de datos lista`, la conexión y esquema funcionan correctamente.

### ✓ Prueba 2: Verificar endpoints REST del Backend

1. Asegúrate de que el backend está ejecutándose (`python main.py`)
2. Espera 2-3 segundos a que inicie completamente
3. Desde PowerShell, prueba los endpoints:

```powershell
# Obtener todas las fincas
Invoke-RestMethod http://localhost:5001/api/fincas/

# Obtener métricas de benchmark
Invoke-RestMethod http://localhost:5001/api/benchmark/filas
Invoke-RestMethod http://localhost:5001/api/benchmark/comparacion

# Resetear métricas de benchmark
Invoke-RestMethod -Method Post http://localhost:5001/api/benchmark/reset
```

### ✓ Prueba 3: Verificar Frontend (interfaz visual)

1. Con `npm run dev` ejecutándose en la carpeta `frontend`
2. Abre `http://localhost:5173` en el navegador
3. Deberías ver:
   - **Conexión WebSocket activa:** Los gráficos se actualizan en tiempo real cada 5 segundos
   - **Lista de fincas:** Aparecen las fincas cargadas desde la BD
   - **Panel de métricas:** Muestran datos de sensores
   - **Panel de benchmarks:** Comparan rendimiento

### ✓ Prueba 4: Verificar simulación en tiempo real

1. Con ambos servicios ejecutándose (backend + frontend)
2. Abre las **DevTools del navegador** (F12) → **Console**
3. Deberías ver logs de conexión WebSocket
4. En el navegador, observa:
   - Los gráficos se actualizan cada 5 segundos
   - Los valores de sensores cambian
   - Las alertas simuladas aparecen ocasionalmente en el panel de alertas

## Estructura del Proyecto

```
Agrostream_sq/
├── backend (Python)
│   ├── main.py              → Punto de entrada del servidor
│   ├── config.py            → Configuración y variables de entorno
│   ├── requirements.txt      → Dependencias Python
│   ├── api/                 → Rutas y endpoints Flask
│   ├── models/              → Modelos de datos (SQLAlchemy)
│   ├── services/            → Lógica de negocio
│   ├── repositories/        → Acceso a base de datos
│   └── simulation/          → Simulador de sensores
│
└── frontend (React + TypeScript)
    ├── package.json
    ├── vite.config.ts
    ├── src/
    │   ├── main.tsx         → Punto de entrada React
    │   ├── App.tsx          → Componente principal
    │   ├── components/      → Componentes React
    │   └── lib/             → Utilidades (API, WebSocket)
    └── index.html
```

## Solución de problemas

### El frontend no recibe datos del backend
- Verifica que el backend está ejecutándose en `http://localhost:5001`
- Abre DevTools (F12) y revisa la pestaña **Network** → **WS** para ver la conexión WebSocket
- Asegúrate de que ambos están en `localhost` (no en `127.0.0.1` o IPs diferentes)

### La base de datos no conecta
- Verifica la URL en `.env` bajo `DATABASE_URL`
- Si usas Neon: verifica conexión a Internet
- Si usas PostgreSQL local: asegúrate de que el servicio está ejecutándose

### Los módulos Python no se encuentran
- Asegúrate de estar en el venv: `.\venv\Scripts\activate`
- Reinstala dependencias: `pip install -r requirements.txt`

### Prueba 3: validar que la simulación inserta lecturas

Después de que el backend esté corriendo, espera al menos 10-15 segundos (por el intervalo por defecto) y vuelve a mirar:

```powershell
Invoke-RestMethod http://localhost:5001/api/benchmark/filas
```

El valor `filas_lecturas` debería empezar a aumentar.

### Prueba 4 (manual recomendada): frontend + WebSocket

1. Levanta backend y frontend.
2. Abre `http://localhost:5173`.
3. Verifica que el panel cargue datos y que el WebSocket se conecte (los gráficos de benchmark y métricas se actualizan en tiempo real).

## Troubleshooting

- Si falla la conexión a PostgreSQL:
  - verifica que `DATABASE_URL` apunte a `agrostream_sq`
  - verifica que el servicio de PostgreSQL esté corriendo
  - verifica credenciales (usuario `postgres` y contraseña `1234`)
- Si el frontend no levanta por errores de import:
  - en este repositorio `frontend/src/main.tsx` importa `./App`; si ese archivo no existe en tu copia, tendrás que crear `frontend/src/App.tsx` o ajustar el import.

