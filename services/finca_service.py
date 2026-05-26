"""
services/finca_service.py — Lógica de negocio para fincas.
Inicialización de datos seed y operaciones de alto nivel.
"""

import config
from repositories.finca_repository import FincaRepository
from typing import Optional, List, Dict, Any


class FincaService:
    """Servicio de negocio para gestión de fincas."""

    def __init__(self):
        self.repo = FincaRepository()

    def inicializar_datos_seed(self):
        """
        Crea las 3 fincas iniciales y sus 27 sensores (9 por finca).
        Se ejecuta al arrancar la aplicación en app_factory.
        Solo inserta si no existen — es idempotente.
        """
        for finca_data in config.FINCAS:
            if not self.repo.existe(finca_data["id"]):
                self.repo.crear_finca(finca_data)
                print(f"  ✓ Finca creada: {finca_data['nombre']}")

            # Crear sensores (idempotente internamente)
            creados = self.repo.crear_sensores_iniciales(finca_data["id"])
            if creados:
                print(f"    → {len(creados)} sensores creados para {finca_data['nombre']}")

    def listar_fincas(self) -> List[Dict[str, Any]]:
        """Retorna todas las fincas activas."""
        return self.repo.obtener_todas()

    def obtener_finca(self, finca_id: str) -> Optional[Dict[str, Any]]:
        """Retorna una finca por ID."""
        return self.repo.obtener_por_id(finca_id)

    def obtener_sensores(self, finca_id: str) -> List[Dict[str, Any]]:
        """Retorna sensores activos de una finca."""
        return self.repo.obtener_sensores(finca_id)
