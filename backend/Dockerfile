FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for pytesseract and pdfplumber
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libpoppler-dev \
    poppler-utils \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
