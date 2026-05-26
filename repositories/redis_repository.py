"""
repositories/redis_repository.py — Repositorio Redis para AgroStream-SQL.
Encapsula operaciones CRUD sobre Redis para lecturas, alertas e historial.
Sigue el esquema de claves definido en models.redis_constants.
"""

import json
from typing import Dict, Any, List, Optional
from utils.redis_client import get_redis_client
from models.redis_constants import (
    sensor_estado_key,
    finca_ultima_key,
    sensor_stream_key,
    alertas_finca_key,
    ALERTAS_GLOBAL,
    TTL_24H,
    HISTORIAL_MAX_LEN,
    ALERTAS_GLOBAL_MAX_LEN,
    ALERTAS_FINCA_MAX_LEN,
)


class RedisRepository:
    """
    Repositorio centralizado para operaciones sobre Redis.
    Maneja:
    - Estado actual de sensores
    - Última lectura por finca
    - Historial de lecturas
    - Alertas globales y por finca
    """

    def __init__(self):
        """Inicializa el cliente Redis."""
        self.client = get_redis_client()

    def guardar_lectura_sensor(self, sensor_id: str, lectura_dict: Dict[str, Any]) -> bool:
        """
        Guarda la lectura actual de un sensor en su estado.

        Args:
            sensor_id (str): ID único del sensor (ej: "finca_001:temperatura:0")
            lectura_dict (Dict): Diccionario con campos de la lectura
                Esperados: {"valor", "unidad", "timestamp", "tipo", "finca_id", ...}

        Returns:
            bool: True si se guardó exitosamente

        Esquema Redis:
            Clave: sensor:{sensor_id}:estado
            Tipo: Hash
            Campos: valor, unidad, timestamp, tipo, finca_id, ...
            TTL: 24 horas
        """
        try:
            clave = sensor_estado_key(sensor_id)
            
            # Convertir valores complejos a strings si es necesario
            mapping = {}
            for k, v in lectura_dict.items():
                if isinstance(v, (dict, list)):
                    mapping[k] = json.dumps(v)
                else:
                    mapping[k] = str(v)
            
            # Insertar o actualizar el hash
            self.client.hset(clave, mapping=mapping)
            
            # Establecer TTL de 24 horas
            self.client.expire(clave, TTL_24H)
            
            return True
        except Exception as e:
            print(f"❌ Error guardando lectura sensor {sensor_id}: {e}")
            return False

    def actualizar_ultima_finca(
        self,
        finca_id: str,
        tipo_sensor: str,
        lectura_json: str,
    ) -> bool:
        """
        Actualiza la última lectura por tipo de sensor para una finca.

        Args:
            finca_id (str): ID de la finca (ej: "finca_001")
            tipo_sensor (str): Tipo de sensor (ej: "temperatura", "humedad", "co2")
            lectura_json (str): JSON string con la lectura completa

        Returns:
            bool: True si se guardó exitosamente

        Esquema Redis:
            Clave: finca:{finca_id}:ultima
            Tipo: Hash
            Campos: {tipo_sensor: lectura_json, ...}
            TTL: 24 horas
        """
        try:
            clave = finca_ultima_key(finca_id)
            
            # Insertar o actualizar el campo en el hash
            self.client.hset(clave, tipo_sensor, lectura_json)
            
            # Establecer TTL de 24 horas
            self.client.expire(clave, TTL_24H)
            
            return True
        except Exception as e:
            print(f"❌ Error actualizando última lectura finca {finca_id}: {e}")
            return False

    def agregar_historial_sensor(
        self,
        sensor_id: str,
        lectura_json: str,
        max_len: Optional[int] = None,
    ) -> bool:
        """
        Agrega una lectura al historial (stream) de un sensor.
        Mantiene las N más recientes (FIFO: nuevas al inicio).

        Args:
            sensor_id (str): ID del sensor
            lectura_json (str): JSON string de la lectura
            max_len (int, optional): Máximo número de elementos. Defaults to HISTORIAL_MAX_LEN.

        Returns:
            bool: True si se agregó exitosamente

        Esquema Redis:
            Clave: sensor:{sensor_id}:stream
            Tipo: List
            Orden: FIFO (lpush al inicio)
            TTL: 24 horas
            Máximo: 500 elementos (recortados con ltrim)
        """
        try:
            if max_len is None:
                max_len = HISTORIAL_MAX_LEN

            clave = sensor_stream_key(sensor_id)

            # Insertar por la cabeza (nuevas primero)
            self.client.lpush(clave, lectura_json)

            # Recortar la lista al tamaño máximo
            # ltrim(clave, 0, max_len-1) mantiene elementos 0 a max_len-1
            self.client.ltrim(clave, 0, max_len - 1)

            # Establecer TTL de 24 horas
            self.client.expire(clave, TTL_24H)

            return True
        except Exception as e:
            print(f"❌ Error agregando historial sensor {sensor_id}: {e}")
            return False

    def agregar_alerta_global(
        self,
        alerta_json: str,
        max_len: Optional[int] = None,
    ) -> bool:
        """
        Agrega una alerta a la cola global.
        Mantiene las N alertas más recientes (FIFO: nuevas al inicio).
        Las alertas globales NO expiran (permanentes).

        Args:
            alerta_json (str): JSON string de la alerta
            max_len (int, optional): Máximo número de elementos. Defaults to ALERTAS_GLOBAL_MAX_LEN.

        Returns:
            bool: True si se agregó exitosamente

        Esquema Redis:
            Clave: alertas:global
            Tipo: List
            Orden: FIFO (lpush al inicio)
            TTL: Ninguno (persistente)
            Máximo: 1000 elementos
        """
        try:
            if max_len is None:
                max_len = ALERTAS_GLOBAL_MAX_LEN

            # Insertar por la cabeza
            self.client.lpush(ALERTAS_GLOBAL, alerta_json)

            # Recortar la lista al tamaño máximo
            self.client.ltrim(ALERTAS_GLOBAL, 0, max_len - 1)

            # NO establecer TTL (alertas globales persisten)

            return True
        except Exception as e:
            print(f"❌ Error agregando alerta global: {e}")
            return False

    def agregar_alerta_finca(
        self,
        finca_id: str,
        alerta_json: str,
        max_len: Optional[int] = None,
    ) -> bool:
        """
        Agrega una alerta a la cola de una finca específica.
        Mantiene las N alertas más recientes de la finca (FIFO: nuevas al inicio).

        Args:
            finca_id (str): ID de la finca
            alerta_json (str): JSON string de la alerta
            max_len (int, optional): Máximo número de elementos. Defaults to ALERTAS_FINCA_MAX_LEN.

        Returns:
            bool: True si se agregó exitosamente

        Esquema Redis:
            Clave: alertas:{finca_id}
            Tipo: List
            Orden: FIFO (lpush al inicio)
            TTL: 24 horas
            Máximo: 200 elementos
        """
        try:
            if max_len is None:
                max_len = ALERTAS_FINCA_MAX_LEN

            clave = alertas_finca_key(finca_id)

            # Insertar por la cabeza
            self.client.lpush(clave, alerta_json)

            # Recortar la lista al tamaño máximo
            self.client.ltrim(clave, 0, max_len - 1)

            # Establecer TTL de 24 horas
            self.client.expire(clave, TTL_24H)

            return True
        except Exception as e:
            print(f"❌ Error agregando alerta finca {finca_id}: {e}")
            return False

    # ──────────────────────────────────────────────
    # Métodos auxiliares de lectura (para futuras tareas)
    # ──────────────────────────────────────────────

    def obtener_estado_sensor(self, sensor_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual de un sensor (todas las claves del hash).

        Args:
            sensor_id (str): ID del sensor

        Returns:
            Dict: Diccionario con campos del sensor, o None si no existe
        """
        try:
            clave = sensor_estado_key(sensor_id)
            datos = self.client.hgetall(clave)
            return datos if datos else None
        except Exception as e:
            print(f"❌ Error obteniendo estado sensor {sensor_id}: {e}")
            return None

    def obtener_ultima_finca(self, finca_id: str) -> Optional[Dict[str, str]]:
        """
        Obtiene las últimas lecturas por tipo de sensor de una finca.

        Args:
            finca_id (str): ID de la finca

        Returns:
            Dict: {tipo_sensor: lectura_json, ...}, o None si no existe
        """
        try:
            clave = finca_ultima_key(finca_id)
            datos = self.client.hgetall(clave)
            return datos if datos else None
        except Exception as e:
            print(f"❌ Error obteniendo última finca {finca_id}: {e}")
            return None

    def obtener_historial_sensor(self, sensor_id: str, limite: int = 50) -> List[str]:
        """
        Obtiene el historial más reciente de un sensor (limitado).

        Args:
            sensor_id (str): ID del sensor
            limite (int): Número máximo de elementos a retornar. Defaults to 50.

        Returns:
            List: Lista de JSON strings de lecturas (más recientes primero)
        """
        try:
            clave = sensor_stream_key(sensor_id)
            datos = self.client.lrange(clave, 0, limite - 1)
            return datos if datos else []
        except Exception as e:
            print(f"❌ Error obteniendo historial sensor {sensor_id}: {e}")
            return []

    def obtener_alertas_global(self, limite: int = 50) -> List[str]:
        """
        Obtiene las alertas globales más recientes (limitadas).

        Args:
            limite (int): Número máximo de elementos a retornar. Defaults to 50.

        Returns:
            List: Lista de JSON strings de alertas (más recientes primero)
        """
        try:
            datos = self.client.lrange(ALERTAS_GLOBAL, 0, limite - 1)
            return datos if datos else []
        except Exception as e:
            print(f"❌ Error obteniendo alertas globales: {e}")
            return []

    def obtener_alertas_finca(self, finca_id: str, limite: int = 50) -> List[str]:
        """
        Obtiene las alertas más recientes de una finca (limitadas).

        Args:
            finca_id (str): ID de la finca
            limite (int): Número máximo de elementos a retornar. Defaults to 50.

        Returns:
            List: Lista de JSON strings de alertas (más recientes primero)
        """
        try:
            clave = alertas_finca_key(finca_id)
            datos = self.client.lrange(clave, 0, limite - 1)
            return datos if datos else []
        except Exception as e:
            print(f"❌ Error obteniendo alertas finca {finca_id}: {e}")
            return []
