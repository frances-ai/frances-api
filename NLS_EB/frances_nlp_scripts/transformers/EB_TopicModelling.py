#!/usr/bin/env python
# coding: utf-8

# # Exploring Terms in the Encyclopaedia Britannica
# 
# ## Similar terms within an edition - BERT - Transformers
# 
# 
# https://theaidigest.in/how-to-do-semantic-document-similarity-using-bert/

# ### Loading the necessary libraries

# In[80]:


import os
from bertopic import BERTopic
import pandas as pd
import pickle
import numpy as np
import umap
import hdbscan
os.environ["TOKENIZERS_PARALLELISM"] = "true"
def get_topic_name(index_uri, topics, topic_model):
    topic_num=topics[index_uri]
    topic_info=topic_model.get_topic(topic_num)
    topic_name=""
    #lets get the first 4 elements
    cont = 0
    for i in topic_info:
        topic_name=topic_name+"_"+i[0]
        cont=cont+1
        if cont == 4:
            break
    topic_name=str(topic_num)+topic_name
    return topic_name


with open('terms_definitions_final.txt', 'rb') as fp:
    documents = pickle.load(fp)

#embeddings = np.load('embeddings_mpnet.npy')
print("phase 1")

# Define UMAP model to reduce embeddings dimension
umap_model = umap.UMAP(n_neighbors=15,
                       n_components=10,
                       min_dist=0.0,
                       metric='cosine',
                       low_memory=False)

# Define HDBSCAN model to perform documents clustering
hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=10,
                                min_samples=1,
                                metric='euclidean',
                                cluster_selection_method='eom',
                                prediction_data=True)
                                

topic_model = BERTopic(top_n_words=20,
                       n_gram_range=(1,2), 
                       calculate_probabilities=True,
                       umap_model= umap_model,
                       hdbscan_model=hdbscan_model,
                       verbose=True)

print("phase 2")
topics, probs = topic_model.fit_transform(documents)

print("phase 3")
t_names=[]
topics_names=[]
for i in range(0, len(topics)):
    topic_name=get_topic_name(i, topics, topic_model)
    if topic_name not in t_names:
        t_names.append(topic_name)
    topics_names.append(topic_name)

#### removing spaces:

topics_names_new=[]
for i in topics_names:
    topics_names_new.append(i.replace(" ", "_"))


t_names_new=[]
for i in t_names:
    t_names_new.append(i.replace(" ", "_"))


topic_model.save("BerTopic_Model_mpnet")
with open('lda_topics_mpnet.txt', 'wb') as fp:
    pickle.dump(topics, fp)

with open('lda_t_names_mpnet.txt', 'wb') as fp:
    pickle.dump(t_names_new, fp)

with open('lda_topics_names_mpnet.txt', 'wb') as fp:
    pickle.dump(topics_names_new, fp)




