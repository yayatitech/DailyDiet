FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY public ./public
COPY scripts ./scripts

ENV PYTHONPATH=/app/backend
WORKDIR /app/backend

EXPOSE 3000

CMD ["sh", "-c", "python init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 3000"]
