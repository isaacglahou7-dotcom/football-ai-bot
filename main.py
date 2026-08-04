from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")


# ==========================
# CACHE POUR ACCELER LE BOT
# ==========================

TEAM_CACHE = {}
MATCH_CACHE = {}

CACHE_TIME = 1800   # 30 minutes



# ==========================
# SERVEUR RENDER
# ==========================

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"Football AI Bot V3.3 running"
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
        f"Server running on {port}"
    )

    server.serve_forever()



# ==========================
# HEADERS API
# ==========================

def api_headers():

    return {
        "X-Auth-Token": FOOTBALL_API_KEY
    }



# ==========================
# COMPETITIONS
# ==========================

COMPETITIONS = [

    "PL",      # Premier League
    "PD",      # La Liga
    "BL1",     # Bundesliga
    "SA",      # Serie A
    "FL1",     # Ligue 1
    "CL",      # Champions League
    "DED",     # Eredivisie
    "PPL",     # Portugal

]



# ==========================
# RECUPERATION MATCHS
# ==========================

def get_matches():

    now = time.time()


    if "matches" in MATCH_CACHE:

        if now - MATCH_CACHE["time"] < CACHE_TIME:

            return MATCH_CACHE["matches"]



    all_matches = []


    for comp in COMPETITIONS:


        url = (
            "https://api.football-data.org/v4/"
            f"competitions/{comp}/matches"
        )


        try:

            response = requests.get(

                url,

                headers=api_headers(),

                params={
                    "status":"SCHEDULED"
                },

                timeout=10
            )


            data = response.json()


            all_matches += data.get(
                "matches",
                []
            )


        except Exception:

            pass



    MATCH_CACHE["matches"] = all_matches

    MATCH_CACHE["time"] = now


    return all_matches



# ==========================
# HISTORIQUE EQUIPE AVEC CACHE
# ==========================

def get_team_history(team):


    now = time.time()


    if team in TEAM_CACHE:


        saved = TEAM_CACHE[team]


        if now - saved["time"] < CACHE_TIME:

            return saved["data"]



    stats = {

        "games":0,
        "wins":0,
        "draws":0,
        "losses":0,
        "goals_for":0,
        "goals_against":0

    }



    for comp in COMPETITIONS:


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


            matches = data.get(
                "matches",
                []
            )


        except:

            continue



        for match in matches:


            home = match["homeTeam"]["name"]

            away = match["awayTeam"]["name"]



            if team not in [home, away]:

                continue



            hg = match["score"]["fullTime"]["home"]

            ag = match["score"]["fullTime"]["away"]



            if hg is None or ag is None:

                continue



            stats["games"] += 1



            if team == home:


                stats["goals_for"] += hg

                stats["goals_against"] += ag



                if hg > ag:

                    stats["wins"] += 1

                elif hg == ag:

                    stats["draws"] += 1

                else:

                    stats["losses"] += 1



            else:


                stats["goals_for"] += ag

                stats["goals_against"] += hg



                if ag > hg:

                    stats["wins"] += 1

                elif ag == hg:

                    stats["draws"] += 1

                else:

                    stats["losses"] += 1



    TEAM_CACHE[team] = {

        "time":now,

        "data":stats

    }


    return stats
    # ==========================
# MOTEUR IA FOOTBALL
# ==========================


def calculate_prediction(home, away):

    home_stats = get_team_history(home)

    away_stats = get_team_history(away)



    # Même si peu de matchs, on utilise les données disponibles

    home_games = max(
        home_stats["games"],
        1
    )

    away_games = max(
        away_stats["games"],
        1
    )



    home_attack = (
        home_stats["goals_for"]
        /
        home_games
    )


    away_attack = (
        away_stats["goals_for"]
        /
        away_games
    )


    home_defense = (
        home_stats["goals_against"]
        /
        home_games
    )


    away_defense = (
        away_stats["goals_against"]
        /
        away_games
    )



    home_power = (

        home_stats["wins"] * 3

        +

        home_attack * 10

        -

        home_defense * 5

        +

        10

    )



    away_power = (

        away_stats["wins"] * 3

        +

        away_attack * 10

        -

        away_defense * 5

    )



    if home_power < 1:

        home_power = 10


    if away_power < 1:

        away_power = 8



    total = (

        home_power

        +

        away_power

        +

        20

    )



    home_win = round(
        home_power / total * 100
    )


    away_win = round(
        away_power / total * 100
    )


    draw = 100 - home_win - away_win



    # Probabilités buts

    avg_goals = (

        home_attack

        +

        away_attack

    )



    over25 = round(
        min(
            85,
            max(
                40,
                avg_goals * 35
            )
        )
    )


    under25 = 100 - over25



    # Both teams score

    gg_yes = round(

        min(
            80,
            max(
                35,
                (
                    home_attack
                    +
                    away_attack
                )
                *
                35
            )
        )

    )


    gg_no = 100 - gg_yes



    # Double chance

    one_x = min(
        99,
        home_win + draw
    )


    x_two = min(
        99,
        away_win + draw
    )


    twelve = min(
        99,
        home_win + away_win
    )



    # Score probable

    home_goals = round(
        home_attack
    )


    away_goals = round(
        away_attack
    )



    if home_goals < 1:

        home_goals = 1


    if away_goals < 1:

        away_goals = 1



    score = (

        f"{home_goals}-{away_goals}"

    )



    return {


        "home":home_win,

        "draw":draw,

        "away":away_win,


        "over25":over25,

        "under25":under25,


        "gg_yes":gg_yes,

        "gg_no":gg_no,


        "1x":one_x,

        "x2":x_two,

        "12":twelve,


        "score":score

    }




# ==========================
# AFFICHAGE RESULTAT
# ==========================


def format_prediction(home, away):


    p = calculate_prediction(
        home,
        away
    )



    return (

        f"⚽ {home} vs {away}\n\n"

        f"🏠 {home}: {p['home']}%\n"

        f"🤝 Nul: {p['draw']}%\n"

        f"✈️ {away}: {p['away']}%\n\n"


        f"⚽ Over 2.5 : {p['over25']}%\n"

        f"⚽ Under 2.5 : {p['under25']}%\n\n"


        f"🥅 GG Oui : {p['gg_yes']}%\n"

        f"🚫 GG Non : {p['gg_no']}%\n\n"


        f"🔄 Double chance:\n"

        f"1X : {p['1x']}%\n"

        f"X2 : {p['x2']}%\n"

        f"12 : {p['12']}%\n\n"


        f"🎯 Score probable : {p['score']}\n"

        "━━━━━━━━━━━━━━\n"

    )
    # ==========================
# COMMANDES TELEGRAM
# ==========================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "⚽ Football AI Bot V3.3 en ligne\n\n"

        "Commandes:\n"

        "/leagues - Compétitions\n"

        "/predict - 20 analyses IA\n"

        "/premier - Premier League\n"

        "/champions - Champions League\n"

        "/ligue1 - Ligue 1\n"

        "/bundesliga - Bundesliga\n"

        "/seriea - Serie A"

    )



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

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
# PREDICTION 20 MATCHS
# ==========================


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):


    await update.message.reply_text(

        "🤖 Analyse IA en cours...\n"

        "⏳ Recherche des matchs"

    )



    matches = get_matches()



    if not matches:


        await update.message.reply_text(

            "❌ Aucun match disponible"

        )

        return



    message = (

        "🤖 PRÉDICTIONS IA DES MATCHS\n\n"

    )



    count = 0



    for match in matches:


        home = match["homeTeam"]["name"]

        away = match["awayTeam"]["name"]



        message += format_prediction(

            home,

            away

        )


        count += 1



        if count >= 20:

            break



    await update.message.reply_text(

        message

    )



# ==========================
# COMMANDES LIGUES
# ==========================


async def premier(update, context):

    await competition_command(
        update,
        "PL"
    )


async def champions(update, context):

    await competition_command(
        update,
        "CL"
    )


async def ligue1(update, context):

    await competition_command(
        update,
        "FL1"
    )


async def bundesliga(update, context):

    await competition_command(
        update,
        "BL1"
    )


async def seriea(update, context):

    await competition_command(
        update,
        "SA"
    )



async def competition_command(update, code):


    matches = get_competition_matches(code)


    text = "🤖 Analyse IA\n\n"


    for match in matches[:20]:


        text += format_prediction(

            match["homeTeam"]["name"],

            match["awayTeam"]["name"]

        )


    await update.message.reply_text(

        text

    )



# ==========================
# LANCEMENT
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
        CommandHandler("predict", predict)
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


    print(
        "🤖 Football AI Bot V3.3 démarré..."
    )


    app.run_polling()



if __name__ == "__main__":

    main()
