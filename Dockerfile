FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY firstmyko_bot/ ./firstmyko_bot/
COPY run_firstmyko_bot.py .
COPY check_discord_connection.py .

CMD ["python", "run_firstmyko_bot.py"]
