"""Caché en memoria con vencimiento, segura para hilos.

Sirve para no gastar cuota de Google en lecturas repetidas (listados de
meses, de planillas o de trabajadores) y para recordar respuestas ya
entregadas (idempotencia de los mensajes del chat).
"""
import threading
import time
from collections import OrderedDict
from typing import Callable, Hashable

_MISSING = object()


class TtlCache:
    def __init__(self, ttl_seconds: float, max_items: int = 1000, clock: Callable[[], float] = time.monotonic):
        self._ttl = ttl_seconds
        self._max_items = max_items
        self._clock = clock
        self._items: OrderedDict[Hashable, tuple[float, object]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: Hashable, default=None):
        with self._lock:
            entry = self._items.get(key, _MISSING)
            if entry is _MISSING:
                return default
            expires_at, value = entry
            if expires_at <= self._clock():
                del self._items[key]
                return default
            return value

    def set(self, key: Hashable, value) -> None:
        with self._lock:
            self._items[key] = (self._clock() + self._ttl, value)
            self._items.move_to_end(key)
            while len(self._items) > self._max_items:
                self._items.popitem(last=False)

    def get_or_load(self, key: Hashable, loader: Callable[[], object]):
        """Devuelve lo guardado o lo carga. Un resultado None no se guarda."""
        value = self.get(key, _MISSING)
        if value is not _MISSING:
            return value
        value = loader()
        if value is not None:
            self.set(key, value)
        return value

    def invalidate(self, predicate: Callable[[Hashable], bool]) -> None:
        with self._lock:
            for key in [k for k in self._items if predicate(k)]:
                del self._items[key]
