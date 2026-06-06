FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p firstmyko_bot
COPY __init__.py bot_main.py config.py knowledge.py ai_responder.py forum_sync.py ./firstmyko_bot/
COPY run_firstmyko_bot.py .
COPY check_discord_connection.py .

CMD ["python", "run_firstmyko_bot.py"]
