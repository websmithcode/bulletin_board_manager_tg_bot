FROM python:3.10-rc

WORKDIR /app/bot

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "bot.py" ]