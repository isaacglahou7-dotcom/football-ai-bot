async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Test API Football en cours..."
    )

    if not FOOTBALL_API_KEY:
        await update.message.reply_text(
            "❌ Clé API Football manquante dans Render."
        )
        return

    url = "https://v3.football.api-sports.io/fixtures"

    params = {
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )

        data = response.json()

        # Afficher la réponse API pour diagnostic
        await update.message.reply_text(
            str(data)[:3000]
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur API : {e}"
        )
