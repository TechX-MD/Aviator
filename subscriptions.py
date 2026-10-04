import json, os, threading
import config

_LOCK = threading.Lock()

def _ensure_dir() -> None:
    os.makedirs(os.path.dirname(config.SUBSCRIPTIONS_FILE) or ".", exist_ok=True)

def _load() -> dict:
    _ensure_dir()
    if not os.path.exists(config.SUBSCRIPTIONS_FILE):
        return {}
    try:
        with open(config.SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}

def _save(data: dict) -> None:
    _ensure_dir()
    tmp = config.SUBSCRIPTIONS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, config.SUBSCRIPTIONS_FILE)

def subscribe(user_id: int) -> None:
    with _LOCK:
        data = _load()
        key = str(user_id)
        row = data.get(key, {})
        row["enabled"] = True
        row.setdefault("last_period", 0)
        data[key] = row
        _save(data)

def unsubscribe(user_id: int) -> None:
    with _LOCK:
        data = _load()
        data.pop(str(user_id), None)
        _save(data)

def get(user_id: int) -> dict:
    with _LOCK:
        return _load().get(str(user_id), {})

def mark_sent(user_id: int, period: int) -> None:
    with _LOCK:
        data = _load()
        key = str(user_id)
        if key in data:
            data[key]["last_period"] = int(period)
            _save(data)

def all_active() -> list:
    with _LOCK:
        data = _load()
    out = []
    for key, row in data.items():
        if row.get("enabled"):
            try:
                out.append((int(key), row))
            except (TypeError, ValueError):
                continue
    return out
