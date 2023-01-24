FROM python:3.10.9-alpine

RUN mkdir "/var/www"

COPY . /var/www

WORKDIR /var/www/

RUN pip install -r requirements.txt

CMD python main.py