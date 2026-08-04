from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# Serveur pour Render
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
        "Commandes :\n"
        "/today - Matchs du jour\n"
        "/help - Aide"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Démarrer le bot\n"
        "/help - Aide\n"
        "/today - Matchs du jour"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Test API Football en cours..."
    )

    if not FOOTBALL_API_KEY:
        await update.message.reply_text(
            "❌ Clé API Football manquante dans Render."
        )
        return

    url = "https://v3.football.api-sports.io/fixtures"

    params = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        data = response.json()

        # Affiche la réponse API pour diagnostic
        await update.message.reply_text(
            str(data)[:3000]
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur API : {e}"
        )


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
