# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
# FROM conda/miniconda3

WORKDIR /app

# install prequisites

RUN apt update
RUN apt -y install build-essential
RUN apt -y install curl

RUN pip install --upgrade pip

# install defoe

COPY ./defoe_lib/requirements.txt defoe-req.txt
RUN pip install -r defoe-req.txt

# COPY ./defoe_lib/requirements.sh defoe-req.sh
# COPY ./defoe_lib/scripts/download_ntlk_corpus.sh ./scripts/download_ntlk_corpus.sh
# RUN bash defoe-req.sh

# install frances

COPY ./frances-api/web_app/requirements.txt frances-req.txt
RUN pip install -r frances-req.txt

# copy code files

COPY ./frances-api ./frances-api
COPY ./defoe_lib ./defoe_lib

# copy default consul config

COPY install_config.sh .
COPY ./data/config.json ./data/config.json

# required ports

EXPOSE 80
EXPOSE 8080
EXPOSE 5000

# entrypoint

COPY start.sh .
RUN chmod +x start.sh

CMD ["bash", "start.sh"] 
