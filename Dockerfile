FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip ca-certificates \
    fonts-liberation libappindicator3-1 libasound2 \
    libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 xdg-utils \
    libu2f-udev && \
    curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb && \
    apt install -y ./chrome.deb && rm chrome.deb

ENV CHROME_BIN=/usr/bin/google-chrome
ENV DISPLAY=:99

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["uvicorn", "Scraper:app", "--host", "0.0.0.0", "--port", "10000"]
