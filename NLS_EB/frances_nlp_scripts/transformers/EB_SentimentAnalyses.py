#!/usr/bin/env python
# coding: utf-8

# ### Loading the necessary libraries

# In[66]:


import yaml
import numpy as np
import collections
import os
import pickle
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline

with open('terms_definitions_final.txt', 'rb') as fp:
    documents = pickle.load(fp)

sentiment_analysis = pipeline("sentiment-analysis",model="siebert/sentiment-roberta-large-english")

tokenizer_long = AutoTokenizer.from_pretrained("mnaylor/bigbird-base-mimic-mortality")
model_long = AutoModelForSequenceClassification.from_pretrained("mnaylor/bigbird-base-mimic-mortality")
sentiment_analysis_long = pipeline("sentiment-analysis",  model=model_long, tokenizer=tokenizer_long)

sentiment_documents=[]
cont=0
for i in documents:
    text=i.lower()
    print("Trying document {}".format(cont))
    try:
        sentiment_documents.append(sentiment_analysis(text))
    except:
        #print("Error in %s" %cont)
        try:
            sentiment_documents.append(sentiment_analysis_long(text))
        except:
            print("Error_2 in %s" %cont)
            sentiment_documents.append([{'label': 'ERROR', 'score': 0.0}])
    cont=cont+1
    
print("FINISH")
with open('terms_sentiments.txt', 'wb') as fp:
    pickle.dump(sentiment_documents, fp)

print("SAVED")
