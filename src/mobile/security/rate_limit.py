"""Límite simple de solicitudes por clave (ventana deslizante, en memoria)."""
import threading
import time
from collections import deque
from typing import Callable, Hashable


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self._max_events = max_events
        self._window = window_seconds
        self._clock = clock
        self._events: dict[Hashable, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: Hashable) -> bool:
        """Registra un evento si cabe en la ventana. False si la clave ya llegó al máximo."""
        now = self._clock()
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= now - self._window:
                events.popleft()
            if len(events) >= self._max_events:
                return False
            events.append(now)
            # Limpieza: no acumular claves viejas para siempre.
            if len(self._events) > 10_000:
                for stale in [k for k, q in self._events.items() if not q or q[-1] <= now - self._window]:
                    del self._events[stale]
            return True
