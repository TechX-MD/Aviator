from __future__ import annotations
import logging
from aiohttp import web
import config, history
from aviator import build_signal, crash_for_period, current_period, fmt_zw, period_start_zw

log = logging.getLogger("aviator-dashboard")

PAGE_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>Aviator Dashboard</title><style>body{background:#0a0b10;color:#fff;font-family:sans-serif;padding:20px}.card{background:#12141d;padding:15px;border-radius:10px;margin-bottom:15px}.big{font-size:35px;color:#f5c451;font-weight:bold}</style></head><body><h1>✈️ Aviator Live Signals</h1><div class="card"><div>Next Multiplier:</div><div class="big" id="p">--</div><div>Confidence: <span id="c">--</span></div><div>Countdown: <span id="cd">--</span>s</div></div><div class="card"><h3>Last Rounds:</h3><div id="h"></div></div><script>async function f(){try{let r=await fetch('/api/state');let d=await r.json();document.getElementById('p').innerText=d.signal.predicted+'x';document.getElementById('c').innerText=d.signal.confidence+'%';document.getElementById('cd').innerText=d.in_seconds;let h=d.history.map(x=>`<div>#${x.period} : <b>${x.value}x</b> (${x.time_zw})</div>`).join('');document.getElementById('h').innerHTML=h;}catch(e){}}setInterval(f,1000);f();</script></body></html>"""

def state_payload() -> dict:
    p = current_period()
    history.record(p - 1, crash_for_period(p - 1))
    sig = build_signal()
    rows = history.last(config.DASHBOARD_HISTORY)
    hist = [{"period": int(r["period"]), "value": round(float(r["value"]), 2), "time_zw": period_start_zw(int(r["period"])).strftime("%H:%M:%S")} for r in rows]
    return {
        "now_zw": fmt_zw(),
        "in_seconds": sig["in_seconds"],
        "signal": sig,
        "history": hist,
    }

async def handle_index(_): return web.Response(text=PAGE_HTML, content_type="text/html")
async def handle_state(_): return web.json_response(state_payload())
async def handle_health(_): return web.json_response({"ok": True})

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/state", handle_state)
    app.router.add_get("/api/health", handle_health)
    return app

async def start_dashboard():
    if not config.DASHBOARD_ENABLED: return None
    runner = web.AppRunner(create_app())
    await runner.setup()
    site = web.TCPSite(runner, config.DASHBOARD_HOST, config.DASHBOARD_PORT)
    await site.start()
    log.info(f"Dashboard on http://{config.DASHBOARD_HOST}:{config.DASHBOARD_PORT}")
    return runner

async def stop_dashboard(runner):
    if runner: await runner.cleanup()
