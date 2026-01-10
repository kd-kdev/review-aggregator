FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy EVERYTHING in this folder
COPY . .

CMD ["python", "steam_fetcher.py"]
