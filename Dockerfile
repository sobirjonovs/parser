FROM python:3.10.9-alpine

RUN mkdir "/var/www"

COPY . /var/www

WORKDIR /var/www/

RUN pip install -r requirements.txt

CMD exec /bin/sh -c "trap : TERM INT; sleep infinity & wait"