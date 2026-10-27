"""Heartbeat фоновых процессов: живой цикл регулярно обновляет файл, healthcheck проверяет возраст.

Процесс может быть жив, но зависнуть в цикле — проверка «контейнер запущен» этого не заметит.
"""

import os
import time
from pathlib import Path


class StaleHeartbeatError(RuntimeError):
    pass


def heartbeat_path(directory: str | Path, service: str) -> Path:
    return Path(directory) / f"{service}.heartbeat"


def write_heartbeat(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(f"{time.time():.3f}\n", encoding="utf-8")
    os.replace(tmp, path)  # атомарно: healthcheck не прочитает недописанный файл


def ensure_fresh_heartbeat(path: Path, max_age_seconds: float) -> float:
    try:
        written = float(path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError) as exc:
        raise StaleHeartbeatError(f"heartbeat missing or invalid: {path}") from exc
    age = max(0.0, time.time() - written)
    if age > max_age_seconds:
        raise StaleHeartbeatError(f"heartbeat is stale: age={age:.1f}s max={max_age_seconds:.1f}s")
    return age
