#!/bin/bash

eval "$(conda shell.bash hook)"
conda create -n py39 python=3.9
conda activate py39

NEW_PYTHON_PATH=/opt/conda/miniconda3/envs/py39/bin/python

echo export PYSPARK_PYTHON=$NEW_PYTHON_PATH >> ~/.bashrc
echo export PYSPARK_DRIVER_PYTHON=$NEW_PYTHON_PATH >> ~/.bashrc

export PYSPARK_PYTHON=$NEW_PYTHON_PATH
export PYSPARK_DRIVER_PYTHON=$NEW_PYTHON_PATH

conda install --yes lxml
conda install --yes nltk
conda install --yes pep8
conda install --yes pylint
#conda install --yes pycodestyle
conda install --yes pytest
conda install --yes PyYAML
conda install --yes regex
conda install --yes requests
conda install --yes pathlib
conda install -c conda-forge spacy
conda install --yes SPARQLWrapper
pip install pandas
pip install google-cloud-storage
pip install lexicalrichness
pip install gender-guesser
python -m spacy download en
python -m spacy download en_core_web_lg
python -m nltk.downloader all

cp -R /root/nltk_data /usr/lib/.
cp -R /root/nltk_data /usr/local/lib/.

gcloud storage cp gs://frances2023/defoe.zip /home/defoe.zip
unzip /home/defoe.zip -d /home