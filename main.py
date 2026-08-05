from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os
import requests
import time
import asyncio
import threading

from datetime import datetime

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

def get_date():

    return datetime.now().strftime("%Y-%m-%d")

def limit(value):

    if value < 0:
        return 0

    if value > 100:
        return 100

    return value

def get_team_form(team_id):

    data = api_get(

        "/fixtures",

        {

            "team": team_id,

            "last": 5

        }

    )

    form = {

        "wins": 0,

        "draws": 0,

        "losses": 0,

        "goals_for": 0,

        "goals_against": 0,

        "points": 0

    }

    if not data.get("response"):

        return form

    for match in data["response"]:

        home = match["teams"]["home"]["id"]

        away = match["teams"]["away"]["id"]

        hg = match["goals"]["home"] or 0

        ag = match["goals"]["away"] or 0

        if team_id == home:

            form["goals_for"] += hg

            form["goals_against"] += ag

            if hg > ag:

                form["wins"] += 1

                form["points"] += 3

            elif hg == ag:

                form["draws"] += 1

                form["points"] += 1

            else:

                form["losses"] += 1

        else:

            form["goals_for"] += ag

            form["goals_against"] += hg

            if ag > hg:

                form["wins"] += 1

                form["points"] += 3

            elif ag == hg:

                form["draws"] += 1

                form["points"] += 1

            else:

                form["losses"] += 1

    return form

def analyze_match(match):

    home = match["teams"]["home"]

    away = match["teams"]["away"]

    home_form = get_team_form(
        home["id"]
    )

    away_form = get_team_form(
        away["id"]
    )

    home_score = (

        home_form["points"]

        + (home_form["wins"] * 2)

        + home_form["goals_for"]

        - home_form["goals_against"]

        + 8

    )

    away_score = (

        away_form["points"]

        + (away_form["wins"] * 2)

        + away_form["goals_for"]

        - away_form["goals_against"]

    )

    if home_score < 1:

        home_score = 1

    if away_score < 1:

        away_score = 1

    total = home_score + away_score

    home_percent = int(
        (home_score / total) * 65 + 15
    )

    away_percent = int(
        (away_score / total) * 65 + 15
    )

    draw_percent = 100 - home_percent - away_percent

    if draw_percent < 15:

        draw_percent = 15

        if home_percent > away_percent:

            home_percent -= 10

        else:

            away_percent -= 10

    home_percent = limit(home_percent)

    away_percent = limit(away_percent)

    draw_percent = limit(draw_percent)

    possibilities = {

        "home": home_percent,

        "draw": draw_percent,

        "away": away_percent

    }

    best = max(
        possibilities,
        key=possibilities.get
    )

    if best == "home":

        prediction = (
            "Victoire "
            + home["name"]
        )

    elif best == "away":

        prediction = (
            "Victoire "
            + away["name"]
        )

    else:

        prediction = "Match nul possible"

    confidence = possibilities[best]

    reason = (

        f"{home['name']} : "

        f"{home_form['wins']}V "

        f"{home_form['draws']}N "

        f"{home_form['losses']}D, "

        f"{home_form['goals_for']} buts marqués. "

        f"{away['name']} : "

        f"{away_form['wins']}V "

        f"{away_form['draws']}N "

        f"{away_form['losses']}D, "

        f"{away_form['goals_for']} buts marqués."

    )

    return {

        "prediction": prediction,

        "home": home_percent,

        "draw": draw_percent,

        "away": away_percent,

        "confidence": confidence,

        "reason": reason

    }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(

        "⚽ Football AI Bot en ligne !\n\n"

        "/today - Matchs du jour\n"

        "/predict - Top prédictions IA"

    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = api_get(

        "/fixtures",

        {

            "date": get_date()

        }

    )

    if not data.get("response"):

        await update.message.reply_text(

            "Aucun match trouvé."

        )

        return

    message = "⚽ MATCHS DU JOUR\n\n"

    for match in data["response"][:15]:

        home = match["teams"]["home"]["name"]

        away = match["teams"]["away"]["name"]

        message += (

            f"🔥 {home} vs {away}\n"

        )

    await update.message.reply_text(message)

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = api_get(

        "/fixtures",

        {

            "date": get_date()

        }

    )

    if not data.get("response"):

        await update.message.reply_text(

            "Aucun match disponible."

        )

        return

    results = []

    for match in data["response"]:

        try:

            analysis = analyze_match(match)

            results.append(

                {

                    "match": match,

                    "analysis": analysis

                }

            )

        except Exception as e:

            print(
                "ERROR:",
                e
            )

    results.sort(

        key=lambda x: x["analysis"]["confidence"],

        reverse=True

    )

    message = "🤖 TOP PRÉDICTIONS IA\n\n"

    count = 0

    for item in results:

        match = item["match"]

        analysis = item["analysis"]

        home = match["teams"]["home"]["name"]

        away = match["teams"]["away"]["name"]

        message += (

            f"⚽ {home} vs {away}\n"

            f"✅ Choix: {analysis['prediction']}\n"

            f"🏠 Domicile: {analysis['home']}%\n"

            f"🤝 Nul: {analysis['draw']}%\n"

            f"✈️ Extérieur: {analysis['away']}%\n"

            f"🎯 Confiance IA: {analysis['confidence']}%\n"

            f"🧠 Analyse: {analysis['reason']}\n\n"

        )

        count += 1

        if count >= 5:

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

            b"Football AI Bot Running"

        )

def run_server():

    server = HTTPServer(

        ("0.0.0.0", PORT),

        Handler

    )

    print(

        "Server running on",

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
