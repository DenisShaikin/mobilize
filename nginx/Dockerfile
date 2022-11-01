FROM nginx:1.23-alpine

RUN rm /etc/nginx/conf.d/default.conf
# RUN rm /etc/nginx/sites-available
COPY default.conf /etc/nginx/conf.d

RUN apt install -y software-properties-common
RUN add-apt-repository ppa:certbot/certbot
RUN apt -y update 
RUN apt install -y certbot