FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ../testing /app/
COPY ../app /app/
ENTRYPOINT ["python", "Indexer.py"]