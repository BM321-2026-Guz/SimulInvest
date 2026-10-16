"""Login deneme sınırı (issue #40).

İki sayaç tutulur, ikisi de sadece HATALI denemeleri sayar:
- IP + e-posta: aynı yerden aynı hesaba şifre denemeyi durdurur. Sadece e-postaya göre
  sayılsaydı, saldırgan başkasının hesabını kasıtlı olarak kilitleyebilirdi.
- IP: tek IP'den çok sayıda hesaba deneme yapılmasını durdurur.

Sayaçlar bellekte tutulur: uygulama yeniden başlayınca sıfırlanır ve birden fazla işlem
(worker) çalışıyorsa her biri kendi sayacını tutar. Bu proje için yeterli.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable

from app.config import settings

Clock = Callable[[], float]
_MAX_KEYS = 10_000  # bellek sınırı: bunu aşınca süresi dolmuş kayıtlar temizlenir


class LoginRateLimiter:
    def __init__(
        self,
        max_per_account: int,
        max_per_ip: int,
        window_seconds: int,
        clock: Clock = time.monotonic,
    ):
        self._limits = {"acct": max_per_account, "ip": max_per_ip}
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _keys(ip: str, email: str) -> dict[str, str]:
        return {"acct": f"acct:{ip}:{email.lower()}", "ip": f"ip:{ip}"}

    def _recent(self, key: str, now: float) -> deque[float]:
        attempts = self._failures.get(key, deque())
        while attempts and attempts[0] <= now - self._window:
            attempts.popleft()
        return attempts

    def retry_after(self, ip: str, email: str) -> int:
        """Engelliyse kaç saniye beklenmesi gerektiğini, değilse 0 döner."""
        now = self._clock()
        wait = 0.0
        with self._lock:
            for kind, key in self._keys(ip, email).items():
                attempts = self._recent(key, now)
                if len(attempts) >= self._limits[kind]:
                    # En eski deneme pencereden çıkınca bir hak açılır.
                    wait = max(wait, attempts[-self._limits[kind]] + self._window - now)
        return math.ceil(wait) if wait > 0 else 0

    def record_failure(self, ip: str, email: str) -> None:
        now = self._clock()
        with self._lock:
            if len(self._failures) > _MAX_KEYS:
                self._prune(now)
            for key in self._keys(ip, email).values():
                attempts = self._recent(key, now)
                attempts.append(now)
                self._failures[key] = attempts

    def record_success(self, ip: str, email: str) -> None:
        # Sadece o hesabın sayacı sıfırlanır; IP sayacı kalır (doğru şifre bilinen bir hesapla
        # diğer hesaplara deneme hakkı kazanılmasın).
        with self._lock:
            self._failures.pop(self._keys(ip, email)["acct"], None)

    def _prune(self, now: float) -> None:
        for key in list(self._failures):
            if not self._recent(key, now):
                del self._failures[key]


_limiter = LoginRateLimiter(
    settings.login_max_attempts,
    settings.login_max_attempts_per_ip,
    settings.login_window_seconds,
)


def get_login_limiter() -> LoginRateLimiter:
    return _limiter
