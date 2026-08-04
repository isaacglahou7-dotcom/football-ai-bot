from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from collections import Counter


BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# ==========================
# SERVEUR RENDER
# ==========================

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



# ==========================
# API FOOTBALL-DATA
# ==========================

def api_headers():
    return {
        "X-Auth-Token": FOOTBALL_API_KEY
    }



# ==========================
# COMPETITIONS
# ==========================

COMPETITIONS = {

    "premier": "PL",

    "champions": "CL",

    "ligue1": "FL1",

    "bundesliga": "BL1",

    "seriea": "SA",

    "eredivisie": "DED",

    "primeira": "PPL",

    "libertadores": "CLI",

    "worldcup": "WC",

    "brasileirao": "BSA",

    "championship": "ELC",

    "laliga": "PD"

}



# ==========================
# ANALYSE IA SIMPLE
# ==========================

def analyse_match(home, away):

    score_home = 50
    score_away = 50


    if len(home) > len(away):
        score_home += 5

    else:
        score_away += 5


    total = score_home + score_away


    home_prob = round(
        score_home / total * 100,
        1
    )

    away_prob = round(
        score_away / total * 100,
        1
    )


    draw_prob = round(
        100 - home_prob - away_prob,
        1
    )


    return (
        f"🤖 Analyse IA\n\n"
        f"🏠 {home}: {home_prob}%\n"
        f"🤝 Nul: {draw_prob}%\n"
        f"✈️ {away}: {away_prob}%"
    )



# ==========================
# RECHERCHE MATCHS
# ==========================

async def send_matches(update, competition):

    url = (
        "https://api.football-data.org/v4/"
        f"competitions/{competition}/matches"
    )


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



    message = "🏆 Matchs trouvés :\n\n"


    for match in matches[:10]:

        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]


        message += (
            f"⚽ {home} vs {away}\n"
        )


    await update.message.reply_text(message)
    # ==========================
# COMMANDES TELEGRAM
# ==========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚽ Football AI Bot V3 en ligne !\n\n"
        "Commandes :\n"
        "/leagues - Compétitions disponibles\n"
        "/premier - Premier League\n"
        "/champions - Champions League\n"
        "/ligue1 - Ligue 1\n"
        "/bundesliga - Bundesliga\n"
        "/seriea - Serie A\n"
        "/eredivisie - Eredivisie\n"
        "/primeira - Primeira Liga\n"
        "/libertadores - Copa Libertadores\n"
        "/worldcup - FIFA World Cup\n"
        "/predict - Analyse IA"
    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏆 Aide Football AI\n\n"
        "/leagues\n"
        "/predict\n"
        "/premier\n"
        "/champions\n"
        "/ligue1\n"
        "/bundesliga\n"
        "/seriea"
    )



async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🏆 Compétitions disponibles :\n\n"
        "🇧🇷 Campeonato Brasileiro Série A\n"
        "🏴 Championship\n"
        "🏴 Premier League\n"
        "🏆 UEFA Champions League\n"
        "🌍 European Championship\n"
        "🇫🇷 Ligue 1\n"
        "🇩🇪 Bundesliga\n"
        "🇮🇹 Serie A\n"
        "🇳🇱 Eredivisie\n"
        "🇵🇹 Primeira Liga\n"
        "🌎 Copa Libertadores\n"
        "🇪🇸 Primera Division\n"
        "🌍 FIFA World Cup"
    )



async def premier(update, context):
    await send_matches(update, "PL")



async def champions(update, context):
    await send_matches(update, "CL")



async def ligue1(update, context):
    await send_matches(update, "FL1")



async def bundesliga(update, context):
    await send_matches(update, "BL1")



async def seriea(update, context):
    await send_matches(update, "SA")



async def eredivisie(update, context):
    await send_matches(update, "DED")



async def primeira(update, context):
    await send_matches(update, "PPL")



async def libertadores(update, context):
    await send_matches(update, "CLI")



async def worldcup(update, context):
    await send_matches(update, "WC")



# ==========================
# PREDICTION IA
# ==========================


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Analyse IA Football\n\n"
        "Pour analyser un match, utilise :\n\n"
        "/predict Équipe1 - Équipe2\n\n"
        "Exemple :\n"
        "/predict Arsenal - Chelsea"
    )


    if context.args:

        match = " ".join(context.args)

        teams = match.split("-")


        if len(teams) == 2:

            home = teams[0].strip()

            away = teams[1].strip()


            result = analyse_match(
                home,
                away
            )


            await update.message.reply_text(
                result
            )



# ==========================
# DEMARRAGE
# ==========================


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
        CommandHandler("leagues", leagues)
    )

    app.add_handler(
        CommandHandler("premier", premier)
    )

    app.add_handler(
        CommandHandler("champions", champions)
    )

    app.add_handler(
        CommandHandler("ligue1", ligue1)
    )

    app.add_handler(
        CommandHandler("bundesliga", bundesliga)
    )

    app.add_handler(
        CommandHandler("seriea", seriea)
    )

    app.add_handler(
        CommandHandler("eredivisie", eredivisie)
    )

    app.add_handler(
        CommandHandler("primeira", primeira)
    )

    app.add_handler(
        CommandHandler("libertadores", libertadores)
    )

    app.add_handler(
        CommandHandler("worldcup", worldcup)
    )

    app.add_handler(
        CommandHandler("predict", predict)
    )


    print("Bot démarré...")

    app.run_polling()



if __name__ == "__main__":
    main()
