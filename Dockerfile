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
COPY /ckeditor/dialogui /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/dialogui
COPY /ckeditor/font /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/font
COPY /ckeditor/richcombo /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/richcombo
COPY /ckeditor/smiley /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/smiley
COPY /ckeditor/bbcode /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/bbcode
COPY /ckeditor/entities /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/entities
COPY /ckeditor/quote /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/quote
COPY /ckeditor/api /usr/local/lib/python3.9/site-packages/flask_ckeditor/static/standard/plugins/api


RUN chmod +x boot.sh

ENV FLASK_APP run.py
ENV FLASK_ENV Production
ENV DEBUG 0

RUN chown -R mobilize:mobilize ./
USER mobilize

EXPOSE 5000

ENTRYPOINT ["./boot.sh"]

