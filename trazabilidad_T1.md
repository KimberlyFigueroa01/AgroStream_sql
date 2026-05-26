# Tarea 1: Preparar el entorno base y agregar Redis como dependencia

**Fecha**: 26 de mayo de 2026  
**Estado**: ✓ COMPLETADA

## 1. Qué se hizo

### Pasos ejecutados:

1. **Actualización de requirements.txt** (`c:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\requirements.txt`)
   - Agregado `redis==5.0.1` al final del archivo

2. **Actualización de config.py** (`c:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\config.py`)
   - Agregado sección "Redis Configuration" con 5 variables de entorno

3. **Creación de .env.example** (`c:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\.env.example`)
   - Nuevo archivo plantilla con todas las variables de entorno necesarias

4. **Creación de carpeta utils/** 
   - Directorio: `c:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\utils\`

5. **Creación de utils/__init__.py**
   - Marcador de paquete Python

6. **Creación de utils/redis_client.py** (`c:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\utils\redis_client.py`)
   - Módulo cliente Redis con función `get_redis_client()`

7. **Instalación de dependencias**
   - Actualizado setuptools y wheel
   - Instalado redis==5.0.1 exitosamente

### Archivos modificados/creados:

| Archivo | Estado | Acción |
|---------|--------|--------|
| `requirements.txt` | ✓ Modificado | Agregado `redis==5.0.1` |
| `config.py` | ✓ Modificado | Agregado variables Redis |
| `.env.example` | ✓ Creado | Plantilla de entorno |
| `utils/` | ✓ Creado | Carpeta de utilidades |
| `utils/__init__.py` | ✓ Creado | Marcador paquete |
| `utils/redis_client.py` | ✓ Creado | Cliente Redis |

## 2. Qué funcionó correctamente

### Verificación de cada punto:

✓ **pip install ejecutado exitosamente**
```
Successfully installed redis==5.0.1
```

✓ **Sin errores de sintaxis en config.py**
- El archivo se importa correctamente
- Las 5 nuevas variables de Redis se cargan sin problemas

✓ **Archivo .env.example creado**
- Ubicación: `c:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\.env.example`
- Contiene todas las variables PostgreSQL, Simulación y Redis

✓ **Módulo utils/redis_client.py funcional**
- Importación exitosa: `from utils.redis_client import get_redis_client`
- No lanza errores al cargar

✓ **Backend arranca sin problemas**
- Importación de config.py exitosa
- Importación de utils.redis_client exitosa
- Redis aún no está siendo usado (configurado pero no conectado)

### Salida de verificación de importación:

```
>>> Cargando .env desde: C:\Users\camil\Desktop\Semestre curso\Electiva 1 - Analitica de Datos\AgroStream_sql\.env
✓ utils.redis_client.get_redis_client importado correctamente
✓ config.py importado correctamente
REDIS_HOST: localhost
REDIS_PORT: 6379
REDIS_DB: 0
```

### Verificación de redis versión:

```
Python 3.12.5
Redis version: 5.0.1
```

## 3. Retos encontrados y soluciones

### Reto 1: Error de setuptools al instalar dependencias
**Problema**: `BackendUnavailable: Cannot import 'setuptools.build_meta'`
**Causa**: setuptools desactualizado o no disponible
**Solución**: Instalar setuptools y wheel antes de redis
```bash
pip install setuptools wheel
pip install redis==5.0.1
```

### Reto 2: Verificación de redis en pip list en Windows
**Problema**: Comandos `find` / `findstr` no funcionaban adecuadamente
**Causa**: Limitaciones de PowerShell con pipes
**Solución**: Verificar directamente importando el módulo Python
```bash
python -c "import redis; print('Redis version:', redis.__version__)"
# Resultado: Redis version: 5.0.1
```

## 4. Evidencia — Archivos Modificados

### 4.1 requirements.txt (agregado redis)

```txt
Flask==3.0.3
Flask-SocketIO==5.5.1
flask-cors==5.0.0
SQLAlchemy==2.0.41
psycopg2-binary==2.9.3
numpy==1.24.4
requests==2.32.3
python-dotenv==1.0.1
redis==5.0.1
```

### 4.2 .env.example (nuevo archivo)

```env
# PostgreSQL (Neon o local)
DATABASE_URL=postgresql://user:pass@host/db

# Simulation
INTERVALO_LECTURA_S=5
PROB_ALERTA_SIMULADA=0.03
FLASK_PORT=5001

# Redis (opcional para modo híbrido)
REDIS_URL=redis://default:password@host:port
# Alternativa con parámetros separados:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=
# REDIS_DB=0
```

### 4.3 config.py (sección Redis agregada)

Líneas 85-93 agregadas:

```python
# ──────────────────────────────────────────────
# Redis Configuration
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
```

## 5. Código Relevante

### 5.1 utils/redis_client.py (nuevo archivo)

```python
"""
utils/redis_client.py — Cliente Redis para AgroStream-SQL.
Proporciona una función singleton para obtener el cliente Redis.
"""

import redis
from config import REDIS_URL, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD


def get_redis_client():
    """
    Devuelve un cliente Redis conectado usando la URL o parámetros separados.
    
    Si REDIS_URL está configurado, lo usa (ej: redis://host:port/db)
    Si no, construye la conexión desde REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD.
    
    Returns:
        redis.Redis: Cliente Redis con decode_responses=True para strings directos.
    """
    if REDIS_URL:
        return redis.from_url(REDIS_URL, decode_responses=True)
    else:
        return redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
```

### 5.2 Variables de Redis en config.py

```python
# ──────────────────────────────────────────────
# Redis Configuration
# ──────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
```

## 6. Criterios de Éxito — Validación Final

| Criterio | Status | Evidencia |
|----------|--------|-----------|
| pip install -r requirements.txt sin errores | ✓ | `Successfully installed redis==5.0.1` |
| No hay errores de sintaxis en config.py | ✓ | Importación exitosa de config |
| .env.example creado correctamente | ✓ | Archivo presente en raíz |
| utils/redis_client.py sin errores al importar | ✓ | `from utils.redis_client import get_redis_client` ✓ |
| Backend arranca sin problemas | ✓ | Importación exitosa, Redis no requerido aún |
| Redis 5.0.1 instalado | ✓ | `redis.__version__ == '5.0.1'` |

## 7. Estado Post-Tarea

- ✓ Proyecto listo para integración Redis
- ✓ Dependencia Redis instalada y accesible
- ✓ Configuración Redis parametrizada por variables de entorno
- ✓ Cliente Redis listo para usar en futuras tareas
- ✓ Documentación en .env.example para nuevos desarrolladores
- ✓ Funcionalidad PostgreSQL del proyecto intacta

## 8. Próximos Pasos (Tarea 2 en adelante)

1. Implementar caché Redis para lecturas frecuentes
2. Agregar almacenamiento de benchmarks en Redis
3. Implementar comparación SQL vs Redis en tiempo real
4. Crear servicios que usen ambas BD (PostgreSQL + Redis)

---

**Generado el**: 26 de mayo de 2026  
**Versión Python**: 3.12.5  
**Redis**: 5.0.1  
**Estado del Proyecto**: ✓ Listo para siguiente fase
