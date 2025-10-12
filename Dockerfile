FROM python:3.10-slim-buster

WORKDIR /web_app

# install prequisites

ENV PYSPARK_PYTHON=/usr/local/bin/python3
ENV PYSPARK_DRIVER_PYTHON=usr/local/bin/python3

# copy requirements
COPY ./web_app/requirements.txt /tmp/requirements.txt

# install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install -U setuptools
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN python -m nltk.downloader all


# required port
EXPOSE 5000

CMD ["sh","start.prod.sh"]
