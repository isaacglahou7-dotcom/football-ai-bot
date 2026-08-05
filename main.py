from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os
import requests
import time
import asyncio
import threading

from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

PORT = int(os.getenv("PORT", 10000))

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

    try:

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

    except Exception as e:

        print("API ERROR:", e)

        return {}

def calculate_percentage(home_score, away_score):

    total = home_score + away_score

    if total == 0:

        return 33, 34, 33

    home = int((home_score / total) * 100)

    away = int((away_score / total) * 100)

    draw = 100 - home - away

    return home, draw, away

def get_team_form(team_id):

    data = api_get(
        "/fixtures",
        {
            "team": team_id,
            "last": 5
        }
    )

    points = 0
    goals_for = 0
    goals_against = 0

    if not data.get("response"):

        return {
            "points": 0,
            "goals_for": 0,
            "goals_against": 0
        }

    for match in data["response"]:

        home = match["teams"]["home"]["id"]

        away = match["teams"]["away"]["id"]

        home_goals = match["goals"]["home"] or 0

        away_goals = match["goals"]["away"] or 0

        if team_id == home:

            goals_for += home_goals

            goals_against += away_goals

            if home_goals > away_goals:
                points += 3

            elif home_goals == away_goals:
                points += 1

        else:

            goals_for += away_goals

            goals_against += home_goals

            if away_goals > home_goals:
                points += 3

            elif away_goals == home_goals:
                points += 1

    return {

        "points": points,

        "goals_for": goals_for,

        "goals_against": goals_against

    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚽ Football AI Bot en ligne !\n\n"
        "/today - Matchs disponibles\n"
        "/predict - Prédictions IA avancées"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = api_get(
        "/fixtures",
        {
            "date": "2026-08-05"
        }
    )

    if not data.get("response"):

        await update.message.reply_text(
            "Aucun match trouvé."
        )

        return

    message = "⚽ MATCHS DISPONIBLES:\n\n"

    count = 0

    for match in data["response"]:

        home = match["teams"]["home"]["name"]

        away = match["teams"]["away"]["name"]

        message += (
            f"🔥 {home} vs {away}\n"
        )

        count += 1

        if count >= 10:

            break

    await update.message.reply_text(message)

def analyse_match(match):

    home = match["teams"]["home"]

    away = match["teams"]["away"]

    home_form = get_team_form(
        home["id"]
    )

    away_form = get_team_form(
        away["id"]
    )

    home_power = (

        home_form["points"]

        + home_form["goals_for"]

        - home_form["goals_against"]

    )

    away_power = (

        away_form["points"]

        + away_form["goals_for"]

        - away_form["goals_against"]

    )

    if home_power < 0:

        home_power = 0

    if away_power < 0:

        away_power = 0

    home_percent, draw_percent, away_percent = calculate_percentage(

        home_power + 10,

        away_power + 10

    )

    if home_percent > away_percent and home_percent > draw_percent:

        choice = (
            "Victoire "
            + home["name"]
        )

        reason = (
            "Meilleure forme récente et avantage domicile."
        )

    elif away_percent > home_percent and away_percent > draw_percent:

        choice = (
            "Victoire "
            + away["name"]
        )

        reason = (
            "Meilleure dynamique récente."
        )

    else:

        choice = "Match nul possible"

        reason = (
            "Les statistiques sont proches."
        )

    return {

        "choice": choice,

        "home_percent": home_percent,

        "draw_percent": draw_percent,

        "away_percent": away_percent,

        "reason": reason

    }

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = api_get(

        "/fixtures",

        {
            "date": "2026-08-05"
        }

    )

    if not data.get("response"):

        await update.message.reply_text(

            "Aucun match disponible."

        )

        return

    message = (

        "🤖 PRÉDICTIONS IA AVANCÉES\n\n"

    )

    analysed = 0

    for match in data["response"]:

        result = analyse_match(match)

        home = match["teams"]["home"]["name"]

        away = match["teams"]["away"]["name"]

        message += (

            f"⚽ {home} vs {away}\n"

            f"📊 Choix: {result['choice']}\n"

            f"🏠 Domicile: {result['home_percent']}%\n"

            f"🤝 Nul: {result['draw_percent']}%\n"

            f"✈️ Extérieur: {result['away_percent']}%\n"

            f"🧠 Analyse: {result['reason']}\n\n"

        )

        analysed += 1

        if analysed >= 10:

            break

    await update.message.reply_text(message)

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)

        self.send_header(
            "Content-type",
            "text/plain"
        )

        self.end_headers()

        self.wfile.write(
            b"Football AI Bot is running"
        )

def run_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        Handler
    )

    print(
        "Server running on port",
        PORT
    )

    server.serve_forever()

async def bot_start():

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
            "today",
            today
        )
    )

    app.add_handler(
        CommandHandler(
            "predict",
            predict
        )
    )

    print(
        "Bot demarre..."
    )

    await app.initialize()

    await app.start()

    await app.updater.start_polling(
        drop_pending_updates=True
    )

    while True:

        await asyncio.sleep(3600)

def run_bot():

    asyncio.run(
        bot_start()
    )

if __name__ == "__main__":

    threading.Thread(

        target=run_server,

        daemon=True

    ).start()

    run_bot()
