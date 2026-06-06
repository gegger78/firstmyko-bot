FROM python:3.12-slim



WORKDIR /app



COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt



RUN mkdir -p firstmyko_bot data

COPY __init__.py bot_main.py config.py knowledge.py ai_responder.py forum_sync.py i18n.py responses.py forum_search.py ./firstmyko_bot/

COPY run_firstmyko_bot.py check_discord_connection.py ./

COPY knowledge_base.json ./data/knowledge_base.json



CMD ["python", "run_firstmyko_bot.py"]


