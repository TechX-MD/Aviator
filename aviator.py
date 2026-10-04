import hashlib
import math
from datetime import datetime, timedelta, timezone
import config

ZW_TZ = timezone(timedelta(hours=config.TZ_OFFSET_HOURS))
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def now_zw() -> datetime:
    return datetime.now(timezone.utc).astimezone(ZW_TZ)

def fmt_zw(dt: datetime | None = None, with_seconds: bool = True) -> str:
    dt = dt or now_zw()
    date_bit = f"{WEEKDAYS[dt.weekday()]}, {dt.day:02d} {dt.strftime('%B %Y')}"
    time_bit = dt.strftime("%H:%M:%S") if with_seconds else dt.strftime("%H:%M")
    return f"{date_bit} · {time_bit}"

def current_period(ts: float | None = None) -> int:
    if ts is None:
        ts = datetime.now(timezone.utc).timestamp()
    return int(ts // config.ROUND_SECONDS)

def seconds_to_next_round(ts: float | None = None) -> int:
    if ts is None:
        ts = datetime.now(timezone.utc).timestamp()
    return int(config.ROUND_SECONDS - (ts % config.ROUND_SECONDS))

def period_start_zw(period: int) -> datetime:
    return datetime.fromtimestamp(period * config.ROUND_SECONDS, tz=timezone.utc).astimezone(ZW_TZ)

def _uniform(seed: str) -> float:
    digest = hashlib.sha256(seed.encode()).digest()
    return int.from_bytes(digest[:8], "big") / float(2 ** 64)

def crash_for_period(period: int) -> float:
    u = _uniform(f"crash:{period}")
    if u < 0.01:
        return 1.00
    value = 0.99 / (1.0 - u)
    value = math.floor(value * 100) / 100.0
    return max(1.00, min(value, 100.0))

def predict(period: int) -> dict:
    next_period = period + 1
    u = _uniform(f"pred:{next_period}")
    raw = config.MIN_MULTIPLIER + (u ** 2.2) * (config.MAX_MULTIPLIER - config.MIN_MULTIPLIER)
    predicted = round(min(max(raw, config.MIN_MULTIPLIER), config.MAX_MULTIPLIER), 2)
    base = 92.0 - (predicted - config.MIN_MULTIPLIER) * 6.5
    jitter = (_uniform(f"conf:{next_period}") - 0.5) * 8.0
    confidence = round(min(max(base + jitter, 52.0), 95.0), 1)

    if predicted < 1.50:
        risk, direction = "Low", "Safe zone"
    elif predicted < 2.50:
        risk, direction = "Medium", "Balanced"
    elif predicted < 4.50:
        risk, direction = "High", "Aggressive"
    else:
        risk, direction = "Very high", "High risk"

    return {
        "period": next_period,
        "predicted": predicted,
        "confidence": confidence,
        "risk": risk,
        "direction": direction,
    }

def build_signal() -> dict:
    period = current_period()
    sig = predict(period)
    sig["time_zw"] = fmt_zw()
    sig["in_seconds"] = seconds_to_next_round()
    sig["current_period"] = period
    return sig
