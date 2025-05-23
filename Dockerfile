FROM python:3.11-slim

# Install Chromium and system deps
RUN apt-get update && apt-get install -y \
    curl unzip wget gnupg chromium chromium-driver \
    fonts-liberation libatk-bridge2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$PATH:/usr/lib/chromium/

WORKDIR /app
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (optional if needed)
RUN python -m playwright install chromium || true

# ✅ Run initial Excel download + parse during build or entrypoint
RUN python download_excel.py && python excel_parser.py

EXPOSE 8080

CMD ["gunicorn", "app_fixed:app", "-b", "0.0.0.0:8080"]
