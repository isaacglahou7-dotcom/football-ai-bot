from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import threading
import requests
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

BOT_TOKEN = os.getenv("BOT_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": FOOTBALL_API_KEY
}

CACHE = {}
CACHE_TIME = 300  # 5 minutes
def api_get(endpoint, params=None):
    key = endpoint + str(params)

    if key in CACHE:
        if time.time() - CACHE[key]["time"] < CACHE_TIME:
            return CACHE[key]["data"]

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
