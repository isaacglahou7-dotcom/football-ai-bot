from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
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
        os.environ.get("PORT", 10000)
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        Handler
    )

    print(f"Server running on port {port}")

    server.serve_forever()



# ==========================
# API FOOTBALL DATA
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
    "laliga": "PD",
    "eredivisie": "DED",
    "primeira": "PPL",
    "championship": "ELC",
    "brasileirao": "BSA",
    "libertadores": "CLI",
    "worldcup": "WC"

}



# ==========================
# MATCHS PAR COMPETITION
# ==========================

def get_competition_matches(code):

    url = (
        "https://api.football-data.org/v4/"
        f"competitions/{code}/matches"
    )

    try:

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

    except:

        return []



# ==========================
# HISTORIQUE EQUIPE CORRIGE
# ==========================

def get_team_history(team):

    stats = {

        "games": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0

    }


    competitions = [

        "PL",
        "PD",
        "BL1",
        "SA",
        "FL1"

    ]


    matches = []


    for comp in competitions:

        url = (
            "https://api.football-data.org/v4/"
            f"competitions/{comp}/matches"
        )


        try:

            response = requests.get(
                url,
                headers=api_headers(),
                params={
                    "status":"FINISHED"
                },
                timeout=10
            )


            data = response.json()


            matches += data.get(
                "matches",
                []
            )


        except:

            pass



    for match in matches:


        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]


        if team not in [home, away]:

            continue



        home_goals = match["score"]["fullTime"]["home"]

        away_goals = match["score"]["fullTime"]["away"]


        if home_goals is None or away_goals is None:

            continue



        stats["games"] += 1



        if team == home:


            stats["goals_for"] += home_goals

            stats["goals_against"] += away_goals



            if home_goals > away_goals:

                stats["wins"] += 1


            elif home_goals == away_goals:

                stats["draws"] += 1


            else:

                stats["losses"] += 1



        else:


            stats["goals_for"] += away_goals

            stats["goals_against"] += home_goals



            if away_goals > home_goals:

                stats["wins"] += 1


            elif away_goals == home_goals:

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


    if home_stats["games"] == 0 or away_stats["games"] == 0:

        return None



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


    total = home_power + away_power


    if total <= 0:

        total = 1



    home_win = round(
        home_power / total * 100
    )


    away_win = round(
        away_power / total * 100
    )


    draw = 100 - home_win - away_win



    total_goals = (

        home_stats["goals_for"]
        +
        away_stats["goals_for"]

    )


    over25 = min(
        85,
        max(
            35,
            total_goals * 8
        )
    )


    under25 = 100 - over25



    gg_yes = min(
        80,
        round(
            (over25 * 0.75)
        )
    )


    gg_no = 100 - gg_yes



    one_x = home_win + draw

    x_two = away_win + draw

    twelve = home_win + away_win



    if home_win > away_win:

        score = "2-1"

    elif away_win > home_win:

        score = "1-2"

    else:

        score = "1-1"



    return {

        "home": home_win,
        "draw": draw,
        "away": away_win,

        "over25": round(over25),
        "under25": round(under25),

        "gg_yes": gg_yes,
        "gg_no": gg_no,

        "1x": one_x,
        "x2": x_two,
        "12": twelve,

        "score": score

    }




# ==========================
# FORMAT MESSAGE IA
# ==========================


def format_prediction(home, away):

    result = calculate_prediction(
        home,
        away
    )


    if result is None:

        return (
            f"⚽ {home} vs {away}\n"
            "❌ Données insuffisantes\n"
        )



    return (

        f"⚽ {home} vs {away}\n\n"

        f"🏠 Victoire {home}: {result['home']}%\n"
        f"🤝 Nul: {result['draw']}%\n"
        f"✈️ Victoire {away}: {result['away']}%\n\n"


        f"⚽ Over 2.5: {result['over25']}%\n"
        f"⚽ Under 2.5: {result['under25']}%\n\n"


        f"🥅 GG Oui: {result['gg_yes']}%\n"
        f"🚫 GG Non: {result['gg_no']}%\n\n"


        f"🔄 Double chance:\n"
        f"1X: {result['1x']}%\n"
        f"X2: {result['x2']}%\n"
        f"12: {result['12']}%\n\n"


        f"🎯 Correct score probable: {result['score']}\n"

        "━━━━━━━━━━━━━━\n"

    )



# ==========================
# COMMANDES TELEGRAM
# ==========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "⚽ Football AI Bot V3.2\n\n"

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
        "/predict - Analyse IA\n"
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
    # ==========================
# RECUPERATION PREDICTIONS
# ==========================


async def competition_matches(update, code):

    matches = get_competition_matches(code)


    if not matches:

        await update.message.reply_text(
            "❌ Aucun match trouvé."
        )

        return



    message = "🤖 ANALYSE IA\n\n"

    count = 0


    for match in matches:


        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]



        message += format_prediction(
            home,
            away
        )


        count += 1


        if count >= 5:

            break



    await update.message.reply_text(
        message
    )



# ==========================
# PREDICT TOUS MATCHS
# ==========================


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Recherche des matchs à analyser..."
    )


    matches = []


    for code in [

        "PL",
        "PD",
        "BL1",
        "SA",
        "FL1"

    ]:

        matches += get_competition_matches(code)



    if not matches:


        await update.message.reply_text(
            "❌ Aucun match disponible."
        )

        return



    message = "🤖 PRÉDICTIONS IA DU JOUR\n\n"



    count = 0



    for match in matches:


        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]



        message += format_prediction(
            home,
            away
        )


        count += 1


        if count >= 5:

            break



    await update.message.reply_text(
        message
    )



# ==========================
# COMMANDES LIGUES
# ==========================


async def premier(update, context):

    await competition_matches(
        update,
        "PL"
    )


async def champions(update, context):

    await competition_matches(
        update,
        "CL"
    )


async def ligue1(update, context):

    await competition_matches(
        update,
        "FL1"
    )


async def bundesliga(update, context):

    await competition_matches(
        update,
        "BL1"
    )


async def seriea(update, context):

    await competition_matches(
        update,
        "SA"
    )


async def laliga(update, context):

    await competition_matches(
        update,
        "PD"
    )



# ==========================
# DEMARRAGE BOT
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
        CommandHandler(
            "start",
            start
        )
    )


    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )


    app.add_handler(
        CommandHandler(
            "leagues",
            leagues
        )
    )


    app.add_handler(
        CommandHandler(
            "predict",
            predict
        )
    )


    app.add_handler(
        CommandHandler(
            "premier",
            premier
        )
    )


    app.add_handler(
        CommandHandler(
            "champions",
            champions
        )
    )


    app.add_handler(
        CommandHandler(
            "ligue1",
            ligue1
        )
    )


    app.add_handler(
        CommandHandler(
            "bundesliga",
            bundesliga
        )
    )


    app.add_handler(
        CommandHandler(
            "seriea",
            seriea
        )
    )


    app.add_handler(
        CommandHandler(
            "laliga",
            laliga
        )
    )


    print(
        "🤖 Football AI Bot V3.2 démarré..."
    )


    app.run_polling()



if __name__ == "__main__":

    main()
