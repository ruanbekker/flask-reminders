FROM python:2.7
RUN apt-get update

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY templates .
COPY static .
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
