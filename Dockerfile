FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb chromium chromium-driver \
    fonts-liberation libatk-bridge2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$PATH:/usr/lib/chromium/

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install chromium || true

EXPOSE 8080

CMD ["gunicorn", "app_fixed:app", "-b", "0.0.0.0:8080"]
