# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster

WORKDIR /app

# install prequisites

RUN apt update

RUN apt -y install build-essential
RUN apt -y install curl


RUN pip install --upgrade pip


ENV PYSPARK_PYTHON /usr/local/bin/python3
ENV PYSPARK_DRIVER_PYTHON /usr/local/bin/python3

# install frances

COPY ./web_app/requirements.txt frances-req.txt
RUN pip install -r frances-req.txt

# copy code files

COPY ./web_app ./web_app

# copy knowledge graphs files
COPY ./knowledge_graphs ./knowledge_graphs

# copy knowledge graphs install file
COPY install_graph.sh .

# required ports

EXPOSE 80
EXPOSE 8080
EXPOSE 5000

# entrypoint

COPY start.sh .
RUN chmod +x start.sh

CMD ["bash", "start.sh"]
