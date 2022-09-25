FROM python/alpine:3.11-rc

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "bot.py" ]