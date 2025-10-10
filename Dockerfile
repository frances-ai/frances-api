FROM python:3.11-bullseye

WORKDIR /web_app

# install prequisites

ENV PYSPARK_PYTHON=/usr/local/bin/python3
ENV PYSPARK_DRIVER_PYTHON=usr/local/bin/python3

# copy requirements
COPY ./web_app/requirements.txt /tmp/requirements.txt

# install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN python -m nltk.downloader all


# required port
EXPOSE 5000


CMD ["gunicorn", "--forwarded-allow-ips", "10.22.10.2,10.22.10.23", "--timeout", "1000", "-w", "8", "-b", ":5000", "query_app:create_app()"]
