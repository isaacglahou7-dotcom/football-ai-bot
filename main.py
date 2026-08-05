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



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "⚽ Football AI Bot en ligne !\n\n"
        "/today - Matchs du jour\n"
        "/predict - Prédictions IA"
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


    message = "⚽ Matchs du jour:\n\n"


    for match in data["response"][:5]:

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]

        message += (
            f"🔥 {home} vs {away}\n"
        )


    await update.message.reply_text(message)
def analyse_team(team_id):

    stats = api_get(
        "/teams/statistics",
        {
            "team": team_id,
            "season": 2025,
            "league": 1
        }
    )

    if not stats.get("response"):
        return 50


    score = 50

    goals = stats["response"].get("goals", {})

    for_avg = goals.get("for", {}).get("average", {})
    against_avg = goals.get("against", {}).get("average", {})


    try:
        if float(for_avg.get("home", 0)) >= 1.5:
            score += 10

        if float(against_avg.get("home", 0)) <= 1:
            score += 10

    except:
        pass


    return min(score, 90)



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


    message = "🤖 PRÉDICTIONS IA AVANCÉES\n\n"


    for match in data["response"][:5]:

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]

        home_id = match["teams"]["home"]["id"]
        away_id = match["teams"]["away"]["id"]


        home_power = analyse_team(home_id)
        away_power = analyse_team(away_id)


        if home_power > away_power:

            result = f"Victoire {home}"
            confidence = home_power


        elif away_power > home_power:

            result = f"Victoire {away}"
            confidence = away_power


        else:

            result = "Match nul possible"
            confidence = 55



        message += (
            f"⚽ {home} vs {away}\n"
            f"📊 Choix: {result}\n"
            f"🎯 Confiance: {confidence}%\n\n"
        )


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

    app = ApplicationBuilder().token(BOT_TOKEN).build()


    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("today", today)
    )

    app.add_handler(
        CommandHandler("predict", predict)
    )


    print("Bot demarre...")


    await app.initialize()
    await app.start()
    await app.updater.start_polling()


    await asyncio.Event().wait()



if __name__ == "__main__":

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()


    asyncio.run(
        bot_start()
    )
