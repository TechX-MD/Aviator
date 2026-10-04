import json, os, threading
from datetime import datetime, timezone
import config

_LOCK = threading.Lock()

def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(config.ROUNDS_LOG_FILE) or ".", exist_ok=True)

def _load() -> list:
    _ensure_dir()
    if not os.path.exists(config.ROUNDS_LOG_FILE):
        return []
    try:
        with open(config.ROUNDS_LOG_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def _save(rows: list) -> None:
    _ensure_dir()
    tmp = config.ROUNDS_LOG_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, config.ROUNDS_LOG_FILE)

def record(period: int, value: float) -> None:
    with _LOCK:
        rows = _load()
        if any(r.get("period") == period for r in rows):
            return
        rows.append({
            "period": int(period),
            "value": round(float(value), 2),
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })
        rows.sort(key=lambda r: r["period"])
        rows = rows[-config.HISTORY_SIZE:]
        _save(rows)

def last(n: int = 10) -> list:
    with _LOCK:
        rows = _load()
    rows.sort(key=lambda r: r["period"], reverse=True)
    return rows[:n]

def stats() -> dict:
    with _LOCK:
        rows = _load()
    values = [r["value"] for r in rows if "value" in r]
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "avg": round(sum(values) / len(values), 2),
        "max": round(max(values), 2),
        "min": round(min(values), 2),
        "under2": round(100.0 * sum(1 for v in values if v < 2.0) / len(values), 1),
        "over5": round(100.0 * sum(1 for v in values if v >= 5.0) / len(values), 1),
    }
