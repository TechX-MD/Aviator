#!/usr/bin/env python3
import asyncio
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest

import config, dashboard, history, subscriptions
from aviator import build_signal, crash_for_period, current_period, fmt_zw, seconds_to_next_round

logging.basicConfig(format="%(asctime)s %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger("aviator-bot")

DISCLAIMER = "⚠️ <i>Educational/Simulation only. Does not guarantee real betting outcomes. 18+.</i>"

def signal_text(sig: dict) -> str:
    return (
        "✈️ <b>AVIATOR SIGNAL — NEXT ROUND</b>\n"
        f"🕒 {sig['time_zw']} · {config.TZ_NAME}\n"
        f"🎯 Period: <code>{sig['period']}</code>\n"
        f"📈 Prediction: <b>{sig['predicted']:.2f}x</b>\n"
        f"🔒 Confidence: <b>{sig['confidence']:.1f}%</b>\n"
        f"⚙️ Risk: {sig['risk']}\n"
        f"⏳ Next round in: <b>{sig['in_seconds']}s</b>\n\n"
        + DISCLAIMER
    )

async def cmd_start(u: Update, _):
    await u.message.reply_text(
        "👋 Welcome to <b>Aviator Signal Bot (Zimbabwe)</b>!\n"
        "Send /predict for signals or /subscribe for alerts.",
        parse_mode=ParseMode.HTML
    )

async def cmd_predict(u: Update, _):
    await u.message.reply_text(signal_text(build_signal()), parse_mode=ParseMode.HTML)

async def cmd_subscribe(u: Update, _):
    subscriptions.subscribe(u.effective_chat.id)
    await u.message.reply_text("✅ Subscribed to automatic alerts every round!", parse_mode=ParseMode.HTML)

async def cmd_unsubscribe(u: Update, _):
    subscriptions.unsubscribe(u.effective_chat.id)
    await u.message.reply_text("🔕 Unsubscribed successfully.", parse_mode=ParseMode.HTML)

async def tick(context: ContextTypes.DEFAULT_TYPE):
    period = current_period()
    finished = period - 1
    history.record(finished, crash_for_period(finished))
    sig = build_signal()
    for user_id, row in subscriptions.all_active():
        if row.get("last_period") == sig["period"]:
            continue
        try:
            await context.bot.send_message(chat_id=user_id, text=signal_text(sig), parse_mode=ParseMode.HTML)
            subscriptions.mark_sent(user_id, sig["period"])
        except Exception:
            pass

async def _post_init(app: Application):
    app.bot_data["runner"] = await dashboard.start_dashboard()

async def _post_shutdown(app: Application):
    await dashboard.stop_dashboard(app.bot_data.get("runner"))

def main():
    if not config.TELEGRAM_BOT_TOKEN or "YOUR_" in config.TELEGRAM_BOT_TOKEN:
        print("\n❌ Chikumbiro: Isa TELEGRAM_BOT_TOKEN mu .env file!\n")
        return

    # Python 3.14 event loop fix
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Wedzera timeout kusvika ku 45 seconds kuti risadonhe panetwork inonoka
    req = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=45.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .request(req)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("predict", cmd_predict))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.job_queue.run_repeating(tick, interval=config.ROUND_SECONDS, first=3)
    log.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
