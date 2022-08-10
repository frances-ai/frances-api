# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

# install prequisites

RUN apt update

RUN apt -y install build-essential
RUN apt -y install curl
RUN apt -y install zip

RUN pip install --upgrade pip
RUN pip install virtualenv
RUN pip install venv-pack

# install java

RUN apt -y install apt-transport-https ca-certificates wget dirmngr gnupg software-properties-common
RUN wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add -
RUN add-apt-repository --yes https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/
RUN apt update
RUN apt -y install adoptopenjdk-8-hotspot

ENV JAVA_HOME /usr/lib/jvm/adoptopenjdk-8-hotspot-amd64/
RUN export JAVA_HOME

# install Python virtual env
# RUN apt -y install python3.8-venv

# install defoe

COPY ./defoe_lib/requirements.txt defoe-req.txt
RUN pip install -r defoe-req.txt

# install frances

COPY ./frances-api/web_app/requirements.txt frances-req.txt
RUN pip install -r frances-req.txt

# copy code files

COPY ./frances-api ./frances-api
COPY ./defoe_lib ./defoe_lib

# prepare defoe_lib module zip

RUN bash ./defoe_lib/build.sh defoe-req.txt ./defoe_lib

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
