FROM nginx:1.23-alpine

RUN apk update && apk add bash

RUN rm /etc/nginx/conf.d/default.conf
COPY default.conf /etc/nginx/conf.d

