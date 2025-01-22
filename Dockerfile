FROM selenium/standalone-chrome
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt


RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libnss3-tools \
    libnspr4 \
    && wget https://storage.googleapis.com/chrome-for-testing-public/132.0.6834.83/linux64/chrome-linux64.zip \
    && unzip chrome-linux64.zip -d /opt/ \
    && mv /opt/chrome-linux64 /opt/google-chrome \
    && ln -s /opt/google-chrome/chrome /usr/bin/google-chrome \
    && wget https://storage.googleapis.com/chrome-for-testing-public/132.0.6834.83/linux64/chromedriver-linux64.zip \
    && unzip chromedriver-linux64.zip -d /opt/ \
    && mv /opt/chromedriver-linux64/chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver \
    && rm chrome-linux64.zip \
    && rm chromedriver-linux64.zip \
    && apt clean

COPY app/ /app/
CMD ["python", "./chrome_test.py"]
