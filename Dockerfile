FROM python:3.8-slim-buster

# TODO: is this the best working directory? Does it matter?
WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

CMD [ "python", "./buzz-bot.py" ]