import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()

TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
TZ_OFFSET_HOURS = int(_get("TZ_OFFSET_HOURS", "2"))
TZ_NAME = "Africa/Harare (UTC+2)"

ROUND_SECONDS = int(_get("ROUND_SECONDS", "60"))
MIN_MULTIPLIER = 1.00
MAX_MULTIPLIER = 10.00

DATA_DIR = _get("DATA_DIR", "data")
SUBSCRIPTIONS_FILE = os.path.join(DATA_DIR, "subscriptions.json")
ROUNDS_LOG_FILE = os.path.join(DATA_DIR, "rounds.json")

ALERT_MIN_MULTIPLIER = float(_get("ALERT_MIN_MULTIPLIER", "1.00"))
HISTORY_SIZE = int(_get("HISTORY_SIZE", "50"))

DASHBOARD_ENABLED = _get("DASHBOARD_ENABLED", "1").lower() not in ("0", "false", "no", "off")
DASHBOARD_HOST = _get("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(_get("DASHBOARD_PORT", "8080"))
DASHBOARD_HISTORY = int(_get("DASHBOARD_HISTORY", "30"))
