# syntax=docker/dockerfile:1

FROM python:3.9-slim-buster

WORKDIR /web_app

# install prequisites


ENV PYSPARK_PYTHON /usr/local/bin/python3
ENV PYSPARK_DRIVER_PYTHON /usr/local/bin/python3

# copy code files
COPY ./web_app /web_app

# install dependencies
RUN pip install -r /web_app/requirements.txt
RUN python -m nltk.downloader all


# required port
EXPOSE 5000


CMD ["gunicorn", "-w", "8", "-b", ":5000", "query_app:create_app()"]
