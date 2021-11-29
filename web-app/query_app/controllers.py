from flask import Flask, render_template, request, jsonify, session
from .flask_app import app
import requests
import traceback
from .sparql_queries import *
from flask_paginate import Pagination, get_page_parameter
import itertools
from itertools import islice
from sklearn.metrics.pairwise import cosine_similarity
from .utils import calculating_similarity_text, get_topic_name, load_data

import numpy as np
import os
import pickle
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from bertopic import BERTopic

########
input_path_embed="/Users/rosafilgueira/HW-Work/NLS-Fellowship/work/frances/web-app/models/all-mpnet-base-v2-summary"

text_embeddings = np.load('/Users/rosafilgueira/HW-Work/NLS-Fellowship/work/frances/web-app/models/all-mpnet-base-v2-summary/embeddings_1ed.npy')
topic_model = BERTopic.load("/Users/rosafilgueira/HW-Work/NLS-Fellowship/work/frances/web-app/models/all-mpnet-base-v2-summary/BerTopic_Model_1ed") 

similarities=load_data(input_path_embed, 'similarities_1ed.txt')
similarities_sorted=load_data(input_path_embed, 'similarities_sorted_1ed.txt')
documents=load_data(input_path_embed, 'documents_1ed.txt')
terms_info=load_data(input_path_embed, 'terms_info_1ed.txt')
uris=load_data(input_path_embed, 'uris_1ed.txt')
topics=load_data(input_path_embed, 'topics_1ed.txt')

t_names=load_data(input_path_embed, 't_names_1ed.txt')
topics_names=load_data(input_path_embed, 'topics_names_1ed.txt')

sentiment_terms=load_data(input_path_embed,'sentiment_documents_1ed.txt') 
clean_documents=load_data(input_path_embed, 'clean_documents_1ed.txt')

#model = SentenceTransformer('bert-base-nli-mean-tokens')
#model = SentenceTransformer('all-MiniLM-L6-v2')
model = SentenceTransformer('all-mpnet-base-v2')


######

@app.route("/", methods=["GET"])
def home_page():
    return render_template('home.html')

@app.route("/term_search/<string:termlink>",  methods=['GET', 'POST'])
@app.route("/term_search",  methods=['GET', 'POST'])
def term_search(termlink=None):
    
    headers=["Year", "Edition", "Volume", "Start Page", "End Page", "Term Type", "Definition/Summary", "Related Terms", "Topic Modelling", "Sentiment_Score"]
    if request.method == "POST":
        if "search" in request.form:
            term = request.form["search"]
        if not term:
            term = "AABAM"
        term=term.upper()
        session['term'] = term
    
    if termlink!=None:
        term = termlink
        session['term'] = term
    else:
        term=session.get('term')
    if not term:
        term = "AABAM"
    results =get_definition(term)
    topics_vis=[]
    for key, value in results.items():
        index_uri=uris.index(key)
        topic_name = topics_names[index_uri]
        score='%.2f'%sentiment_terms[index_uri][0]['score']
        sentiment = sentiment_terms[index_uri][0]['label']+"_"+score
        if topics[index_uri] not in topics_vis:
            topics_vis.append(topics[index_uri])
        #topic_name = get_topic_name(index_uri, topics, topic_model)
        value.append(topic_name)
        value.append(sentiment)
    if len(topics_vis) >= 1:
        fig1=topic_model.visualize_barchart(topics_vis, n_words=10)
        bar_plot = fig1.to_json() 
    else:
        bar_plot=None
    if len(topics_vis) >= 2:
        fig2=topic_model.visualize_heatmap(topics_vis)
        heatmap_plot = fig2.to_json()
    else:
        heatmap_plot=None
 
    page = int(request.args.get("page", 1))
    page_size=2
    per_page = 2
    offset = (page-1) * per_page
    limit = offset+per_page
    results_for_render=dict(islice(results.items(),offset, limit))
    pagination = Pagination(page=page, total=len(results), per_page=page_size, search=False)
    return render_template("results.html", results=results_for_render,
                                           pagination = pagination, 
                                           headers=headers,
                                           term=term, bar_plot=bar_plot, heatmap_plot=heatmap_plot)
       

@app.route("/eb_details",  methods=['GET', 'POST'])
def eb_details():
    edList=get_editions()
    if 'edition_selection' in request.form and 'volume_selection' in request.form:
        ed_raw=request.form.get('edition_selection')
        vol_raw=request.form.get('volume_selection')
        if vol_raw !="" and ed_raw !="":
            ed_uri="<"+ed_raw+">"
            ed_r=get_editions_details(ed_uri)
            vol_uri="<"+vol_raw+">"
            ed_v=get_volume_details(vol_uri)
            ed_st=get_vol_statistics(vol_uri)
            ed_name=edList[ed_raw]
            vol_name=get_vol_by_vol_uri(vol_uri)
            return render_template('eb_details.html', edList=edList,  ed_r=ed_r, ed_v=ed_v, ed_st=ed_st, ed_name=ed_name, vol_name=vol_name)
        else:
            return render_template('eb_details.html', edList=edList)
    return render_template('eb_details.html', edList=edList)

   

 

@app.route("/vol_details", methods=['GET', 'POST'])
def vol_details():
    if request.method == "POST":
        uri_raw=request.form.get('edition_selection')
        uri="<"+uri_raw+">"
        volList=get_volumes(uri)
        OutputArray = []
        for key, value in sorted(volList.items(), key=lambda item: item[1]):
            outputObj = { 'id':key , 'name': value }
            OutputArray.append(outputObj)
    return jsonify(OutputArray)



@app.route("/visualization_resources", methods=['GET', 'POST'])
def visualization_resources(termlink=None, termtype=None):
    if request.method == "POST":
        if 'resource_uri' in request.form:
            uri_raw=request.form.get('resource_uri').strip().replace("<","").replace(">","")
            if uri_raw == "":
                uri="<https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0>"
            else:
                uri="<"+uri_raw+">"
            g_results=describe_resource(uri)
            return render_template('visualization_resources.html', g_results=g_results, uri=uri)
    else:
        termlink  = request.args.get('termlink', None)
        termtype  = request.args.get('termtype', None)
        if termlink!=None:
            if ">" in termlink:
                termlink=termlink.split(">")[0]
            uri="<https://w3id.org/eb/i/"+termtype+"/"+termlink+">"
            g_results=describe_resource(uri)
            return render_template('visualization_resources.html', g_results=g_results, uri=uri)
        else:
            return render_template('visualization_resources.html')


@app.route("/similar", methods=["GET"])
def similar():
    return render_template('similar.html')


@app.route("/similar_terms", methods=["GET", "POST"])
def similar_terms(termlink=None):
    uri=""
    uri_raw=""
    data_similar=""
    topics_vis=[]
    termlink  = request.args.get('termlink', None)
    termtype  = request.args.get('termtype', None)
    if termlink!=None:
        if ">" in termlink:
            termlink=termlink.split(">")[0]
        uri="<https://w3id.org/eb/i/"+termtype+"/"+termlink+">"
        uri_raw=uri.replace("<","").replace(">","")
        session['uri_raw'] = uri_raw
        session['uri'] = uri
        session["data_similar"] = ""

    elif 'resource_uri' in request.form:
        data_similar=request.form.get('resource_uri')
        if "https://" in data_similar or "w3id" in data_similar:
            uri_raw=data_similar.strip().replace("<","").replace(">","")
        elif data_similar == "":
            uri_raw="https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0"
        else:
            uri_raw=""
            session['uri_raw'] = "free_search"
        if uri_raw!="":
            uri="<"+uri_raw+">"
            session['uri_raw'] = uri_raw
        session['uri'] = uri
        session["data_similar"] = data_similar

    if not uri:
        uri=session.get('uri')      
        uri_raw=session.get('uri_raw')
        data_similar = session.get('data_similar')
      
    if "free_search" in uri_raw:
        results, topics_vis=calculating_similarity_text(data_similar,text_embeddings, model, terms_info, documents,uris, topics_names,topics, sentiment_terms)
              
    else:
        term, definition, enum, year, vnum  =get_document(uri)
        index_uri=uris.index(uri_raw)
        t_name=topics_names[index_uri]
        score='%.2f'%sentiment_terms[index_uri][0]['score']
        t_sentiment = sentiment_terms[index_uri][0]['label']+"_"+score
        results={}
        topics_vis=[]
        for i in range(-2, -22, -1):
            similar_index=similarities_sorted[index_uri][i]
            rank=similarities[index_uri][similar_index]
            score='%.2f'%sentiment_terms[similar_index][0]['score']
            sentiment = sentiment_terms[similar_index][0]['label']+"_"+score
            topic_name = topics_names[similar_index]
            if topics[similar_index] not in topics_vis:
               topics_vis.append(topics[similar_index])
            results[uris[similar_index]]=[terms_info[similar_index][1],terms_info[similar_index][2], terms_info[similar_index][4], terms_info[similar_index][0], documents[similar_index], topic_name, rank, sentiment]
    if len(topics_vis) >= 1:
        fig1=topic_model.visualize_barchart(topics_vis, n_words=10)
        bar_plot = fig1.to_json()
    else:
        bar_plot=None
    if len(topics_vis) >= 2:
        fig2=topic_model.visualize_heatmap(topics_vis)
        heatmap_plot = fig2.to_json()
    else:
        heatmap_plot=None
             
    #### Pagination ###  
    page = int(request.args.get("page", 1))
    page_size=10
    per_page = 10
    offset = (page-1) * per_page
    limit = offset+per_page
    results_for_render=dict(islice(results.items(),offset, limit))
    pagination = Pagination(page=page, total=len(results), per_page=page_size, search=False)
    ##############  
    if "free_search" in uri_raw:
        return render_template('results_similar.html',  results=results_for_render, pagination=pagination,
                                bar_plot=bar_plot, heatmap_plot=heatmap_plot)
    else:
        return render_template('results_similar.html', results=results_for_render, pagination=pagination, 
                                term=term, definition=definition, uri=uri_raw, 
                                enum=enum, year=year, vnum=vnum, t_name=t_name, 
                                bar_plot=bar_plot, heatmap_plot=heatmap_plot, t_sentiment=t_sentiment)
    

@app.route("/topic_modelling", methods=["GET", "POST"])
def topic_modelling(topic_name=None):
    topic_name  = request.args.get('topic_name', None)
    num_topics=len(t_names)
    if topic_name == None:
        if 'topic_name' in request.form:
            topic_name=request.form.get('topic_name')
            if topic_name=="":
                topic_name="0_markettown_miles_sends_members"
            else:
                if topic_name not in t_names:
                    full_topic_name=""
                    number=topic_name+"_"
                    for x in t_names:
                        if x.startswith(number):
                            full_topic_name=x
                    if full_topic_name:
                        topic_name=full_topic_name
                    else:
                        topic_name="0_markettown_miles_sends_members"
            session['topic_name'] = topic_name

    if not topic_name:
         topic_name=session.get('topic_name')
    if not topic_name:
        return render_template('topic_modelling.html', num_topics=num_topics)
    indices = [i for i, x in enumerate(topics_names) if x == topic_name]
    results={}
    for t_i in indices:
        score='%.2f'%sentiment_terms[t_i][0]['score']
        sentiment = sentiment_terms[t_i][0]['label']+"_"+score
        results[uris[t_i]]=[terms_info[t_i][1],terms_info[t_i][2], terms_info[t_i][4], terms_info[t_i][0], documents[t_i], sentiment]
    num_results=len(indices)
    first_topic=topics[indices[0]]
    fig1=topic_model.visualize_barchart([first_topic], n_words=10)
    bar_plot = fig1.to_json()

    #### Pagination ###  
    page = int(request.args.get("page", 1))
    page_size=10
    per_page = 10
    offset = (page-1) * per_page
    limit = offset+per_page
    results_for_render=dict(islice(results.items(),offset, limit))
    pagination = Pagination(page=page, total=len(results), per_page=page_size, search=False)
    ##############  
    return render_template('topic_modelling.html', topic_name=topic_name, 
                                    results=results_for_render, pagination=pagination, 
                                    bar_plot=bar_plot, num_results=num_results, num_topics=num_topics) 
            

@app.route("/spelling_checker", methods=["GET", "POST"])
def spelling_checker(termlink=None):
    uri_raw=""
    uri=""
    termlink  = request.args.get('termlink', None)
    termtype  = request.args.get('termtype', None)
    if termlink!=None:
        if ">" in termlink:
            termlink=termlink.split(">")[0]
        uri="<https://w3id.org/eb/i/"+termtype+"/"+termlink+">"
        uri_raw=uri.replace("<","").replace(">","")

    elif 'resource_uri' in request.form:
        uri_checker=request.form.get('resource_uri')
        print("uri_checker")
        if "https://" in uri_checker or "w3id" in uri_checker:
            uri_raw=uri_checker.strip().replace("<","").replace(">","")
            uri="<"+uri_raw+">"
        elif uri_checker == "":
            uri_raw="https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0"
            uri="<"+uri_raw+">"

    if not uri:
        return render_template('spelling_checker.html')
    else:
        term, definition, enum, year, vnum=get_document(uri)
        index_uri=uris.index(uri_raw)
        clean_definition=clean_documents[index_uri]
        results={}
        results[uri_raw]=[enum,year, vnum, term]
        return render_template('spelling_checker.html',results=results, clean_definition=clean_definition, definition=definition)

@app.route("/evolution_of_terms", methods=["GET"])
def evolution_of_terms():
    return render_template('evolution.html')

@app.route("/defoe_queries", methods=["GET"])
def defoe_queries():
    return render_template('defoe.html')
