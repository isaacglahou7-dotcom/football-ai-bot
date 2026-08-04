from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


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


def headers():
    return {
        "X-Auth-Token": FOOTBALL_API_KEY
    }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Football AI Bot en ligne !\n\n"
        "Commandes :\n"
        "/today - Matchs du jour\n"
        "/next - Prochains matchs (30 jours)\n"
        "/leagues - Compétitions\n"
    )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚽ Recherche des matchs du jour..."
    )

    url = "https://api.football-data.org/v4/matches"

    response = requests.get(
        url,
        headers=headers()
    )

    data = response.json()
    matches = data.get("matches", [])

    if not matches:
        await update.message.reply_text(
            "Aucun match aujourd'hui."
        )
        return

    text = "⚽ Matchs du jour :\n\n"

    for m in matches[:20]:
        text += (
            f"🏟 {m['homeTeam']['name']} "
            f"vs {m['awayTeam']['name']}\n"
        )

    await update.message.reply_text(text)



async def next_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📅 Recherche des prochains matchs..."
    )

    start_date = datetime.now().strftime("%Y-%m-%d")
    end_date = (
        datetime.now() + timedelta(days=30)
    ).strftime("%Y-%m-%d")


    url = (
        "https://api.football-data.org/v4/matches"
        f"?dateFrom={start_date}&dateTo={end_date}"
    )


    response = requests.get(
        url,
        headers=headers()
    )


    data = response.json()
    matches = data.get("matches", [])


    if not matches:
        await update.message.reply_text(
            "Aucun match programmé dans les 30 prochains jours."
        )
        return


    text = "📅 Prochains matchs :\n\n"


    for m in matches[:30]:
        text += (
            f"⚽ {m['homeTeam']['name']} "
            f"vs {m['awayTeam']['name']}\n"
        )


    await update.message.reply_text(text)



async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://api.football-data.org/v4/competitions"


    response = requests.get(
        url,
        headers=headers()
    )


    data = response.json()

    competitions = data.get(
        "competitions",
        []
    )


    text = "🏆 Compétitions disponibles :\n\n"


    for c in competitions[:30]:
        text += f"• {c['name']}\n"


    await update.message.reply_text(text)



def main():

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()


    app = ApplicationBuilder().token(
        BOT_TOKEN
    ).build()


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("today", today)
    )

    app.add_handler(
        CommandHandler("next", next_matches)
    )

    app.add_handler(
        CommandHandler("leagues", leagues)
    )


    print("Bot démarré...")
    app.run_polling()



if __name__ == "__main__":
    main()
