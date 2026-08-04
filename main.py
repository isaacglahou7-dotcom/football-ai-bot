from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
import math
from http.server import BaseHTTPRequestHandler, HTTPServer


BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# ==========================
# SERVEUR RENDER
# ==========================

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            b"Football AI Bot is running"
        )


def run_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        Handler
    )

    print(
        f"Server running on port {port}"
    )

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
# RECUPERATION MATCHS
# ==========================


def get_competition_matches(code):

    url = (
        "https://api.football-data.org/v4/"
        f"competitions/{code}/matches"
    )


    response = requests.get(
        url,
        headers=api_headers(),
        timeout=10
    )


    data = response.json()


    return data.get(
        "matches",
        []
    )



# ==========================
# STATISTIQUES EQUIPES
# ==========================


def get_team_history(team):

    url = (
        "https://api.football-data.org/v4/"
        "matches"
    )


    response = requests.get(
        url,
        headers=api_headers(),
        params={
            "status": "FINISHED"
        },
        timeout=10
    )


    data = response.json()

    matches = data.get(
        "matches",
        []
    )


    stats = {

        "games": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0

    }



    for match in matches:

        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]


        if team not in [
            home,
            away
        ]:
            continue



        hs = match["score"]["fullTime"]["home"]

        as_ = match["score"]["fullTime"]["away"]



        if hs is None or as_ is None:
            continue



        stats["games"] += 1



        if team == home:

            stats["goals_for"] += hs

            stats["goals_against"] += as_


            if hs > as_:
                stats["wins"] += 1

            elif hs == as_:
                stats["draws"] += 1

            else:
                stats["losses"] += 1



        else:

            stats["goals_for"] += as_

            stats["goals_against"] += hs


            if as_ > hs:
                stats["wins"] += 1

            elif as_ == hs:
                stats["draws"] += 1

            else:
                stats["losses"] += 1



    return stats



# ==========================
# MOTEUR ANALYSE IA
# ==========================


def calculate_prediction(home, away):

    home_stats = get_team_history(home)

    away_stats = get_team_history(away)



    if (
        home_stats["games"] == 0
        or away_stats["games"] == 0
    ):

        return (
            "❌ Pas assez de données"
        )



    home_power = (
        home_stats["wins"] * 3
        + home_stats["goals_for"]
        - home_stats["goals_against"]
        + 5
    )


    away_power = (
        away_stats["wins"] * 3
        + away_stats["goals_for"]
        - away_stats["goals_against"]
    )



    total = (
        home_power
        +
        away_power
    )

    if total <= 0:
        total = 1



    home_win = round(
        home_power / total * 100
    )


    away_win = round(
        away_power / total * 100
    )


    draw = (
        100
        -
        home_win
        -
        away_win
    )



    return {
        "home": home_win,
        "draw": draw,
        "away": away_win,
        "over25": min(
            90,
            home_stats["goals_for"]
            +
            away_stats["goals_for"]
        ),
    }
    # ==========================
# AFFICHAGE ANALYSE COMPLETE
# ==========================


def format_prediction(home, away):

    result = calculate_prediction(
        home,
        away
    )


    if isinstance(result, str):
        return result


    home_p = result["home"]
    draw_p = result["draw"]
    away_p = result["away"]


    # Double chance

    one_x = home_p + draw_p
    x_two = away_p + draw_p
    twelve = home_p + away_p


    # Over / Under estimation

    over25 = result["over25"]

    under25 = 100 - over25


    # GG estimation

    gg_yes = min(
        85,
        round(
            (over25 * 0.7)
        )
    )

    gg_no = 100 - gg_yes



    # Score probable simple

    if home_p > away_p:

        score = "2-1"

    elif away_p > home_p:

        score = "1-2"

    else:

        score = "1-1"



    return (

        f"⚽ {home} vs {away}\n\n"

        f"🏠 Victoire {home}: {home_p}%\n"
        f"🤝 Nul: {draw_p}%\n"
        f"✈️ Victoire {away}: {away_p}%\n\n"

        f"⚽ Over 2.5: {over25}%\n"
        f"⚽ Under 2.5: {under25}%\n\n"

        f"🥅 GG Oui: {gg_yes}%\n"
        f"🚫 GG Non: {gg_no}%\n\n"

        f"🔄 Double chance:\n"
        f"1X: {one_x}%\n"
        f"X2: {x_two}%\n"
        f"12: {twelve}%\n\n"

        f"🎯 Correct score probable: {score}\n"

    )



# ==========================
# COMMANDES TELEGRAM
# ==========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "⚽ Football AI Bot V3.1 en ligne\n\n"

        "Commandes:\n"
        "/leagues\n"
        "/predict\n"
        "/premier\n"
        "/champions\n"
        "/ligue1\n"
        "/bundesliga\n"
        "/seriea"

    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "/leagues - Compétitions\n"
        "/predict - Prédictions IA\n"
        "/premier - Premier League\n"
        "/champions - Champions League\n"
        "/ligue1 - Ligue 1\n"
        "/bundesliga - Bundesliga\n"
        "/seriea - Serie A"

    )



async def leagues(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "🏆 Compétitions disponibles:\n\n"

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



async def competition_matches(update, code):

    matches = get_competition_matches(code)



    if not matches:

        await update.message.reply_text(
            "❌ Aucun match trouvé."
        )

        return



    text = "🤖 Prédictions IA\n\n"


    count = 0


    for match in matches:

        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]


        prediction = format_prediction(
            home,
            away
        )


        text += prediction + "\n"


        count += 1


        if count >= 5:
            break



    await update.message.reply_text(
        text
    )



async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Recherche des matchs à analyser..."
    )


    # Toutes les compétitions principales

    matches = []


    for code in [
        "PL",
        "PD",
        "BL1",
        "SA",
        "FL1"
    ]:

        matches += get_competition_matches(
            code
        )



    if not matches:

        await update.message.reply_text(
            "❌ Aucun match disponible."
        )

        return



    text = "🤖 ANALYSE IA DES MATCHS\n\n"


    for match in matches[:5]:

        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]


        text += format_prediction(
            home,
            away
        )

        text += "\n----------------\n"



    await update.message.reply_text(
        text
    )
    # ==========================
# COMMANDES COMPETITIONS
# ==========================


async def premier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "PL")


async def champions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "CL")


async def ligue1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "FL1")


async def bundesliga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "BL1")


async def seriea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "SA")


async def laliga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "PD")


async def eredivisie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "DED")


async def brasileirao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "BSA")


async def championship(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "ELC")


async def libertadores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "CLI")


async def worldcup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await competition_matches(update, "WC")



# ==========================
# LANCEMENT BOT
# ==========================


def main():

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()


    app = ApplicationBuilder().token(
        BOT_TOKEN
    ).build()



    # Commandes principales

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
        CommandHandler("predict", predict)
    )



    # Ligues

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
        CommandHandler("laliga", laliga)
    )

    app.add_handler(
        CommandHandler("eredivisie", eredivisie)
    )

    app.add_handler(
        CommandHandler("brasileirao", brasileirao)
    )

    app.add_handler(
        CommandHandler("championship", championship)
    )

    app.add_handler(
        CommandHandler("libertadores", libertadores)
    )

    app.add_handler(
        CommandHandler("worldcup", worldcup)
    )


    print("🤖 Football AI Bot V3.1 démarré...")

    app.run_polling()



if __name__ == "__main__":
    main()
