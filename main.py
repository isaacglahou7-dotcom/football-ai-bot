from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# Serveur Render
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


def api_headers():
    return {
        "X-Auth-Token": FOOTBALL_API_KEY
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Football AI Bot est en ligne !\n\n"
        "Commandes disponibles :\n"
        "/today - Matchs du jour\n"
        "/next - Prochains matchs\n"
        "/leagues - Ligues disponibles\n"
        "/help - Aide"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/today - Matchs du jour\n"
        "/next - Prochains matchs\n"
        "/leagues - Compétitions disponibles\n"
        "/help - Aide"
    )


# Matchs du jour
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚽ Recherche des matchs du jour..."
    )

    url = "https://api.football-data.org/v4/matches"

    try:
        response = requests.get(
            url,
            headers=api_headers(),
            timeout=10
        )

        data = response.json()
        matches = data.get("matches", [])

        if not matches:
            await update.message.reply_text(
                "Aucun match trouvé aujourd'hui."
            )
            return

        message = "⚽ Matchs du jour :\n\n"

        for match in matches[:15]:
            message += (
                f"🏟 {match['homeTeam']['name']} "
                f"vs {match['awayTeam']['name']}\n"
            )

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur : {e}"
        )


# Prochains matchs
async def next_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📅 Recherche des prochains matchs..."
    )

    date_from = datetime.now().strftime("%Y-%m-%d")
    date_to = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    url = (
        "https://api.football-data.org/v4/matches"
        f"?dateFrom={date_from}&dateTo={date_to}"
    )

    try:
        response = requests.get(
            url,
            headers=api_headers(),
            timeout=10
        )

        data = response.json()
        matches = data.get("matches", [])

        if not matches:
            await update.message.reply_text(
                "Aucun prochain match disponible."
            )
            return

        message = "📅 Prochains matchs :\n\n"

        for match in matches[:20]:
            message += (
                f"⚽ {match['homeTeam']['name']} "
                f"vs {match['awayTeam']['name']}\n"
            )

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur : {e}"
        )


# Compétitions disponibles
async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://api.football-data.org/v4/competitions"

    try:
        response = requests.get(
            url,
            headers=api_headers(),
            timeout=10
        )

        data = response.json()

        competitions = data.get("competitions", [])

        if not competitions:
            await update.message.reply_text(
                "Aucune compétition trouvée."
            )
            return

        message = "🏆 Compétitions disponibles :\n\n"

        for comp in competitions[:20]:
            message += f"• {comp['name']}\n"

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur : {e}"
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
    app.add_handler(CommandHandler("next", next_matches))
    app.add_handler(CommandHandler("leagues", leagues))

    print("Bot démarré...")
    app.run_polling()


if __name__ == "__main__":
    main()
