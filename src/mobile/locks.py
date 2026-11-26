"""Locks asíncronos por clave (administrador, planilla por crear, ...)."""
import asyncio
from typing import Hashable


class KeyedLocks:
    """Un `asyncio.Lock` por clave.

    Con la clave del administrador, sus mensajes de la app se procesan de a
    uno y en orden (como WhatsApp hace por remitente). Con la clave
    (negocio, nombre de planilla), dos toques seguidos en "Crear" no duplican
    el archivo en Drive.
    """

    def __init__(self):
        self._locks: dict[Hashable, asyncio.Lock] = {}

    def get(self, key: Hashable) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()
        return lock
