from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os, yaml
from .defoe_query_utils import preprocess_word, parse_preprocess_word_type
from web_app.query_app.flask_config import DefaultFlaskConfig

import matplotlib.pyplot as plt
from io import BytesIO
import base64

import pandas as pd
import plotly.express as px

import numpy as np
import json


def get_kg_type(collection, source_provider="NLS"):
    return DefaultFlaskConfig.KG_TYPES_MAP[collection][source_provider]


def get_kg_url(kg_type):
    kg_base_url = DefaultFlaskConfig.KG_BASE_URL
    return kg_base_url + kg_type + "/sparql"


###
def load_data(input_path_embed, file_name):
    with open (os.path.join(input_path_embed, file_name), 'rb') as fp:
        data = pickle.load(fp)
    return data

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

def calculating_similarity_text(definition, text_embeddings, model, terms_info, documents, uris, topics_names, topics, sentiment_terms, index_uri=-1):
    definition_embedding= model.encode(definition, batch_size = 8, show_progress_bar = True)
    similarities=cosine_similarity( [definition_embedding], text_embeddings)
    similarities_sorted = similarities.argsort()
    results={}
    topics_vis=[]
    if index_uri < 0:
        end_range=-21
    else:
        end_range=-22
    for i in range(-1, end_range, -1):
        similar_index=similarities_sorted[0][i]
        if ((index_uri >= 0) and (index_uri !=similar_index)) or (index_uri < 0):
            rank=similarities[0][similar_index]
            score='%.2f'%sentiment_terms[similar_index][0]['score']
            sentiment = sentiment_terms[similar_index][0]['label']+"_"+score
            topic_name = topics_names[similar_index]
            if topics[similar_index] not in topics_vis:
                topics_vis.append(topics[similar_index])
            results[uris[similar_index]]=[terms_info[similar_index][1],terms_info[similar_index][2], terms_info[similar_index][4], terms_info[similar_index][0], documents[similar_index], topic_name, rank, sentiment]
    return results, topics_vis


def retrieving_similariy(paraphrases_index, doc_key, paraphrases):
    results=[]
    for key in range(0, len(paraphrases_index)):
        if paraphrases_index[key] == doc_key:
            results.append(paraphrases[key])
    return results

def preprocess_lexicon(data_file, preprocess="normalize"):
    keysentences=[]
    preprocess_type=parse_preprocess_word_type(preprocess)
    with open(data_file, 'r') as f:
        for keysentence in list(f):
            k_split = keysentence.split()
            sentence_word = [preprocess_word(word,preprocess_type) for word in k_split]
            sentence_norm = ''
            for word in sentence_word:
                if sentence_norm == '':
                    sentence_norm = word
                else:
                    sentence_norm += " " + word
            keysentences.append(sentence_norm)
    return keysentences


def dict_defoe_queries():
    defoe_q={}
    defoe_q["frequency_keysearch_by_year"]="frequency_keysearch_by_year"
    defoe_q["publication_normalized"]="publication_normalized"
    defoe_q["uris_keysearch"]="uris_keysearch"
    defoe_q["snippet_keysearch_by_year"]="snippet_keysearch_by_year"
    defoe_q["fulltext_keysearch_by_year"]="fulltext_keysearch_by_year"
    defoe_q["geoparser_by_year"] = "geoparser_by_year"
    defoe_q["frequency-distribution"] = "frequency-distribution"
    defoe_q["lexicon-diversity"] = "lexicon-diversity"
    defoe_q["person_entity_recognition"] = "person_entity_recognition"
    return defoe_q


def read_results(results_file):
    with open(results_file, "r") as stream:
            results=yaml.safe_load(stream)
    return results



def freq_count(results):
    freq_count={}
    for year in results:
        for i in results[year]:
            if i[0] not in freq_count:
                freq_count[i[0]]={}
                freq_count[i[0]][year]=i[1]
                
            else:
                if year not in freq_count[i[0]]:
                    freq_count[i[0]][year]=i[1]
                else:    
                    freq_count[i[0]][year]+=i[1]
    return freq_count


def plot_freq_count(freq_results, view_terms):
    img = BytesIO()
    years=set()
    for term in view_terms:
        if term in freq_results:
            plt.plot(*zip(*sorted(freq_results[term].items())), label=term, lw = 2, alpha = 1, marker="X")
            for y in freq_results[term].keys(): 
                years.add(y)     
    plt.xticks(sorted(list(years)), rotation=50)
    #plt.ticklabel_format(axis="y"style = 'plain')
    plt.legend(loc='upper right')
    plt.ylabel('Frequency')
    plt.xlabel("Years")
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    return plot_url

def normalize_freq(publication, freq_results, view_terms):
    normed_results = {}
    for term in view_terms:
        if term in freq_results:
            normed_results[term]={}
            for year in freq_results[term]:
                normed_results[term][year] = (freq_results[term][year]* len(term.split()))/float(publication[int(year)][2])
    return normed_results


def plotly_norm_freq_count(normalize_f_count):
    df=pd.DataFrame.from_dict(normalize_f_count)
    fig = px.line(df, labels={
                     "index": "Year",
                     "value": "Normalized Frequency",
                     "variable": "Lexicon"
                 }, title="Normalized Frequency of Lexicon Terms per Years")
    fig.update_layout( yaxis = dict(
        showexponent = 'all',
        exponentformat = 'e'))
    return fig

def plotly_freq_count(f_count):
    df=pd.DataFrame.from_dict(f_count)
    fig = px.line(df, labels={
                     "index": "Year",
                     "value": "Frequency",
                     "variable": "Lexicon"
                 }, title="Frequency of Lexicon Terms per Years")
    return fig

def plot_taxonomy_freq(taxonomy, results, norm_publication):

    ### frequency plot
    f_count=freq_count(results)
    plot_f=plotly_freq_count(f_count)

    ### normalize frequency plot
    normalize_f_count=normalize_freq(norm_publication, f_count, taxonomy)
    plot_n_f=plotly_norm_freq_count(normalize_f_count)

    return plot_f, plot_n_f

def pagination_to_dict(p):
  return {
    "page": p.page,
    "total": p.total,
    "perPage": p.per_page,
    "search": p.search,
  }

def sanitize_results(results):
  sanitized = {}
  for key, val in results.items():
      sanitized[key] = sanitize_array(val)
  return sanitized

def sanitize_array(items):
  sanitized = []
  for value in items:
      if type(value) is np.float32:
          # convert numpy float to python float
          sanitized.append(value.item())
          continue
      sanitized.append(value)
  return sanitized

def figure_to_dict(fig):
  if fig is None:
    return None
  # hack to get Figure as dict
  str_data = fig.to_json()
  dict_data = json.loads(str_data)
  return dict_data
