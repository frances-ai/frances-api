#!/usr/bin/env python
import numpy as np
import collections
import pandas as pd
from summarizer import Summarizer, TransformerSummarizer
import pickle
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from collections import Counter
from heapq import nlargest

print("-------")

with open ('topics_definitions.txt', 'rb') as fp:
    topics_documents = pickle.load(fp)
with open('topics_details.txt', 'rb') as fp2:
    topics_info = pickle.load(fp2)
with open('topics_uris.txt', 'rb') as fp3:
    topics_uris = pickle.load(fp3)

indices_ed=["1_1771","1_1773","2","3", "3_supplement", "4",\
             "5","6","7", "8"]

print("Phase 1")
model = TransformerSummarizer(transformer_type="XLNet",transformer_model_key="xlnet-base-cased")
print("Phase 2")
for ed in indices_ed:
   print("ED is %s" % ed)
   filename='indices_%s.txt'%(ed)
   with open(filename, 'rb') as fp4:
       indices= pickle.load(fp4)
   topics_summary=[]
   cont=0
   for i in indices:
       print("Summary %s-%s" %(ed, cont))
       text=topics_documents[i]
       try:
           full = ''.join(model(text, min_length=60, max_length=300))
           topics_summary.append(full)
       except:
           print("Error in %s" %cont)
           topics_summary.append(["Not avaiable"])
       cont=cont+1
    
   print("FINISH TOPICS FOR %s" % ed)
   filename='topics_summary_%s.txt'%(ed)
   with open(filename, 'wb') as fp:
       pickle.dump(topics_summary, fp)
