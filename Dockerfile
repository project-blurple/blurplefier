FROM python:3.7

WORKDIR /app
ADD requirements.txt /app

RUN pip install -r requirements.txt
