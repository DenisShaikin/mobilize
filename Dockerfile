FROM python:3.9-slim-bullseye

# Environment variables, setting app home path and copy of the python app in the container
ENV PYTHONUNBUFFERED True

ENV APP_HOME /home/mobilize  
WORKDIR $APP_HOME
RUN useradd mobilize
RUN chown -R mobilize:mobilize ./
# ./

COPY . ./

# Update/upgrade the system
RUN apt -y update
RUN apt -y upgrade

RUN apt install -y netcat

# WORKDIR /home/mobilize

copy requirements.txt requirements.txt
# RUN python -m venv venv 
# RUN venv/bin/pip install -r requirements.txt

RUN pip install -r requirements.txt
RUN pip install gunicorn pymysql

COPY apps apps
COPY media media
# COPY migrations migrations
COPY run.py boot.sh  ./ 

RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx/default.conf /etc/nginx/conf.d

RUN chmod +x boot.sh

ENV FLASK_APP run.py
ENV FLASK_ENV Production
ENV DEBUG 0

RUN chown -R mobilize:mobilize ./
USER mobilize

EXPOSE 5000

ENTRYPOINT ["./boot.sh"]

