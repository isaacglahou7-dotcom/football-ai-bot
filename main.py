from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# Petit serveur pour Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Football AI Bot is running")


def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Server running on port {port}")
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Football AI Bot est en ligne !\n\n"
        "Tape /help pour voir les commandes."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Démarrer le bot\n"
        "/help - Aide\n"
        "/today - Matchs du jour"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Recherche des matchs du jour..."
    )

    if not FOOTBALL_API_KEY:
        await update.message.reply_text(
            "❌ Clé API Football manquante."
        )
        return

    url = "https://v3.football.api-sports.io/fixtures"

    params = {
        "date": "2026-08-04"
    }

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    data = response.json()

    if not data.get("response"):
        await update.message.reply_text(
            "Aucun match trouvé aujourd'hui."
        )
        return

    message = "⚽ Matchs du jour :\n\n"

    for match in data["response"][:10]:
        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]

        message += f"🏟 {home} vs {away}\n"

    await update.message.reply_text(message)


def main():
    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))

    print("Bot démarré...")
    app.run_polling()


if __name__ == "__main__":
    main()
