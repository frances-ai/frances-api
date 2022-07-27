# syntax=docker/dockerfile:1

# FROM python:3.8-slim-buster

FROM conda/miniconda3
WORKDIR /app

# install prequisites

RUN apt update
RUN apt -y install build-essential

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

COPY ./frances-api .
COPY ./defoe_lib .
CMD [ "python3", "-m" , "frances-api.web_app"]

