"""
utils/redis_client.py — Cliente Redis para AgroStream-SQL.
Proporciona una función singleton para obtener el cliente Redis.
"""

import redis
from config import (
    REDIS_URL,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    REDIS_USERNAME,
    REDIS_PASSWORD,
)


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
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
