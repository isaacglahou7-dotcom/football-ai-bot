from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

print("TOKEN OK:", BOT_TOKEN is not None)
print("API KEY OK:", FOOTBALL_API_KEY is not None)

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": FOOTBALL_API_KEY
}

CACHE = {}
CACHE_TIME = 300


def api_get(endpoint, params=None):
    key = endpoint + str(params)

    if key in CACHE:
        if time.time() - CACHE[key]["time"] < CACHE_TIME:
            return CACHE[key]["data"]

    response = requests.get(
        BASE_URL + endpoint,
        headers=HEADERS,
        params=params,
        timeout=20
    )

    data = response.json()

    CACHE[key] = {
        "time": time.time(),
        "data": data
    }

    return data


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Football AI Bot en ligne !\n\n"
        "/today - Matchs du jour\n"
        "/predict - Prédictions"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = api_get("/fixtures", {"date": "2026-08-04"})

    if not data.get("response"):
        await update.message.reply_text("Aucun match trouvé.")
        return

    message = "⚽ Matchs du jour:\n\n"

    for match in data["response"][:5]:
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]
        message += f"🔥 {home} vs {away}\n"

    await update.message.reply_text(message)


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Analyse IA en préparation..."
    )


if __name__ == "__main__":
    print("Démarrage du bot...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("predict", predict))

    app.run_polling()
