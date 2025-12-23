FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for some Python packages (matplotlib, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libfreetype6-dev libpng-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app_fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
