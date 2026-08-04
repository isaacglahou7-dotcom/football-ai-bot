from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer


BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# =====================
# SERVEUR RENDER
# =====================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Football AI Bot is running")


def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(
        ("0.0.0.0", port),
        Handler
    )
    print(f"Server running on port {port}")
    server.serve_forever()


# =====================
# API FOOTBALL DATA
# =====================

def api_headers():
    return {
        "X-Auth-Token": FOOTBALL_API_KEY
    }


async def send_matches(update, competition):

    url = (
        "https://api.football-data.org/v4/"
        f"competitions/{competition}/matches"
    )

    try:

        response = requests.get(
            url,
            headers=api_headers(),
            timeout=10
        )

        data = response.json()

        matches = data.get(
            "matches",
            []
        )


        if not matches:
            await update.message.reply_text(
                "⚽ Aucun match trouvé pour cette compétition."
            )
            return


        text = "⚽ Matchs trouvés :\n\n"


        for match in matches[:15]:

            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]

            text += (
                f"🏟 {home} "
                f"vs {away}\n"
            )


        await update.message.reply_text(text)


    except Exception as e:

        await update.message.reply_text(
            f"❌ Erreur API : {e}"
        )



# =====================
# COMMANDES TELEGRAM
# =====================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚽ Football AI Bot en ligne !\n\n"
        "Commandes :\n"
        "/premier\n"
        "/liga\n"
        "/bundesliga\n"
        "/seriea\n"
        "/ligue1\n"
        "/predict"
    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "/premier - Premier League\n"
        "/liga - Liga Espagne\n"
        "/bundesliga - Allemagne\n"
        "/seriea - Serie A\n"
        "/ligue1 - Ligue 1\n"
        "/predict - Analyse IA"
    )



async def premier(update, context):

    await send_matches(
        update,
        "PL"
    )



async def liga(update, context):

    await send_matches(
        update,
        "PD"
    )



async def bundesliga(update, context):

    await send_matches(
        update,
        "BL1"
    )



async def seriea(update, context):

    await send_matches(
        update,
        "SA"
    )



async def ligue1(update, context):

    await send_matches(
        update,
        "FL1"
    )



async def predict(update, context):

    await update.message.reply_text(
        "🤖 Analyse IA activée.\n\n"
        "Fonction en préparation :\n"
        "- Forme des équipes\n"
        "- Buts marqués\n"
        "- Classement\n"
        "- Probabilités"
    )



# =====================
# DEMARRAGE
# =====================


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
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("premier", premier)
    )

    app.add_handler(
        CommandHandler("liga", liga)
    )

    app.add_handler(
        CommandHandler("bundesliga", bundesliga)
    )

    app.add_handler(
        CommandHandler("seriea", seriea)
    )

    app.add_handler(
        CommandHandler("ligue1", ligue1)
    )

    app.add_handler(
        CommandHandler("predict", predict)
    )


    print("Bot démarré...")
    app.run_polling()



if __name__ == "__main__":
    main()
