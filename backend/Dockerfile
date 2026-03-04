FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

RUN chmod +x start.sh

# start.sh runs migrations then starts uvicorn.
# $PORT is assigned by Railway at runtime — must not be hardcoded.
CMD ["./start.sh"]
