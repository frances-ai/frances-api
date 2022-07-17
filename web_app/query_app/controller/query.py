from flask import Flask, Blueprint, render_template, send_file, request, jsonify, session
from flask_paginate import Pagination
from http import HTTPStatus
import requests
import traceback
from .sparql_queries import *
import itertools
from itertools import islice
from sklearn.metrics.pairwise import cosine_similarity

from .utils import calculating_similarity_text, get_topic_name, retrieving_similariy
from .utils import plot_taxonomy_freq, preprocess_lexicon, dict_defoe_queries, read_results
from .utils import pagination_to_dict

import os, yaml
import pickle
from tqdm import tqdm
from zipfile import *
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from operator import itemgetter

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from io import BytesIO
import base64

from ..resolver import get_models
from flasgger import swag_from

######### PATHS
defoe_path="/../../defoe"

query = Blueprint("query", __name__, url_prefix="/api/v1/query")
models = get_models()


@query.route("/term_search/<string:termlink>",  methods=['GET'])
@query.route("/term_search",  methods=['POST'])
@swag_from("../docs/query/term_search.yml")
def term_search(termlink=None):
    if request.method == "POST":
        if "search" in request.form:
            term = request.form["search"]
        else:
            term = "AABAM"
        term=term.upper()
        session['term'] = term

    if termlink!=None:
        term = termlink
        session['term'] = term
    else:
        term=session.get('term')

    headers=["Year", "Edition", "Volume", "Start Page", "End Page", "Term Type", "Definition/Summary", "Related Terms", "Topic Modelling", "Sentiment_Score", "Advanced Options"]

    results =get_definition(term, models.documents, models.uris)
    topics_vis=[]
    for key, value in results.items():
        try:
            index_uri=models.uris.index(key)
            topic_name = models.topics_names[index_uri]
            score='%.2f'%models.sentiment_terms[index_uri][0]['score']
            if "LABEL_0" in models.sentiment_terms[index_uri][0]['label']:
               label="POSITIVE"
               sentiment = label+"_"+score
            elif "LABEL_1" in models.sentiment_terms[index_uri][0]['label']:
               label="NEGATIVE"
               sentiment = label+"_"+score
            else:
                sentiment = models.sentiment_terms[index_uri][0]['label']+"_"+score
            if models.topics[index_uri] not in topics_vis:
                topics_vis.append(models.topics[index_uri])
            topic_name = get_topic_name(index_uri, models.topics, models.topic_model)
            topic_name=topic_name.replace(" ", "_")
            print("---- topic_name is %s" % topic_name)
            value.append(topic_name)
            value.append(sentiment)
            value.append(key)
        except:
             pass
    if len(topics_vis) >= 1:
        fig1=models.topic_model.visualize_barchart(topics_vis, n_words=10)
        bar_plot = fig1.to_json()
    else:
        bar_plot=None
    if len(topics_vis) >= 2:
        fig2=models.topic_model.visualize_heatmap(topics_vis)
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
    
    return jsonify({
        "results": results_for_render,
        "pagination": pagination_to_dict(pagination),
        "headers": headers,
        "term": term,
    }), HTTPStatus.OK
    # return TermSearchResponse(
    #   # bar_plot=bar_plot,
    #   # heatmap_plot=heatmap_plot,
    # ).encode()


@query.route("/eb_details",  methods=['GET', 'POST'])
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


@query.route("/vol_details", methods=['GET', 'POST'])
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


@query.route("/visualization_resources", methods=['GET', 'POST'])
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


@query.route("/similar_terms", methods=["GET", "POST"])
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
        results, topics_vis=calculating_similarity_text(data_similar,models.text_embeddings, model, models.terms_info, models.documents, models.uris, models.topics_names, models.topics, models.sentiment_terms, -1)

    else:
        term, definition, enum, year, vnum  =get_document(uri)
        index_uri=models.uris.index(uri_raw)
        t_name=models.topics_names[index_uri]
        score='%.2f'%models.sentiment_terms[index_uri][0]['score']
        if "LABEL_0" in models.sentiment_terms[index_uri][0]['label']:
            label="POSITIVE"
            t_sentiment = label+"_"+score
        elif "LABEL_1" in models.sentiment_terms[index_uri][0]['label']:
            label="NEGATIVE"
            t_sentiment = label+"_"+score
        else:
            t_sentiment = models.sentiment_terms[index_uri][0]['label']+"_"+score

        print("----> index_uri is %s" %index_uri)
        results={}
        #results_sim_first=retrieving_similariy(paraphrases_index_first, index_uri, paraphrases)
        #r_similar_index=[]
        #for r_sim in results_sim_first:
        #    rank, i, similar_index = r_sim
        #    r_similar_index.append(similar_index)
        #    print(similar_index)
        #    score='%.2f'%models.sentiment_terms[similar_index][0]['score']
        #    if "LABEL_0" in models.sentiment_terms[similar_index][0]['label']:
        #       label="POSITIVE"
        #       sentiment = label+"_"+score
        #    elif "LABEL_1" in models.sentiment_terms[similar_index][0]['label']:
        #       label="NEGATIVE"
        #       sentiment = label+"_"+score
        #    else:
        #        sentiment = models.sentiment_terms[similar_index][0]['label']+"_"+score
        #    topic_name = models.topics_names[similar_index]
        #    if topics[similar_index] not in topics_vis:
        #        topics_vis.append(topics[similar_index])
        #    results[uris[similar_index]]=[models.terms_info[similar_index][1],models.terms_info[similar_index][2], models.terms_info[similar_index][4], models.terms_info[similar_index][0], documents[similar_index], topic_name, rank, sentiment]
        #results_sim_second=retrieving_similariy(paraphrases_index_second, index_uri, paraphrases)
        #for r_sim in results_sim_second:
        #    rank, similar_index, j = r_sim
        #    if similar_index not in r_similar_index:
        #        r_similar_index.append(similar_index)
        #        print(similar_index)
        #        score='%.2f'%models.sentiment_terms[similar_index][0]['score']
        #        if "LABEL_0" in models.sentiment_terms[similar_index][0]['label']:
        #            label="POSITIVE"
        #            sentiment = label+"_"+score
        #        elif "LABEL_1" in models.sentiment_terms[similar_index][0]['label']:
        #            label="NEGATIVE"
        #            sentiment = label+"_"+score
        #        else:
        #            sentiment = models.sentiment_terms[similar_index][0]['label']+"_"+score
        #        topic_name = models.topics_names[similar_index]
        #        if topics[similar_index] not in topics_vis:
        #            topics_vis.append(topics[similar_index])
        #        results[uris[similar_index]]=[models.terms_info[similar_index][1],models.terms_info[similar_index][2], models.terms_info[similar_index][4], models.terms_info[similar_index][0], documents[similar_index], topic_name, rank, sentiment]
        #if len(r_similar_index)==0:
        results, topics_vis=calculating_similarity_text(definition,models.text_embeddings, models.model, models.terms_info, models.documents, models.uris, models.topics_names, models.topics, models.sentiment_terms, index_uri)
    if len(topics_vis) >= 1:
        fig1=models.topic_model.visualize_barchart(topics_vis, n_words=10)
        bar_plot = fig1.to_json()
    if len(topics_vis) >= 1:
        fig1=models.topic_model.visualize_barchart(topics_vis, n_words=10)
        bar_plot = fig1.to_json()
    else:
        bar_plot=None
    if len(topics_vis) >= 2:
        fig2=models.topic_model.visualize_heatmap(topics_vis)
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


@query.route("/topic_modelling", methods=["GET", "POST"])
def topic_modelling(topic_name=None):
    topic_name  = request.args.get('topic_name', None)
    num_topics=len(models.t_names)-2
    if topic_name == None:
        if 'topic_name' in request.form:
            topic_name=request.form.get('topic_name')
            if topic_name=="":
                topic_name="0_hindustan_of_hindustan_hindustan_in_district"
            else:
                if topic_name not in models.t_names:
                    full_topic_name=""
                    number=topic_name+"_"
                    for x in models.t_names:
                        if x.startswith(number):
                            full_topic_name=x
                    if full_topic_name:
                        topic_name=full_topic_name
                    else:
                        topic_name="0_hindustan_of_hindustan_hindustan_in_district"
            session['topic_name'] = topic_name

    if not topic_name:
         topic_name=session.get('topic_name')
    if not topic_name:
        return render_template('topic_modelling.html', num_topics=num_topics)
    indices = [i for i, x in enumerate(models.topics_names) if x == topic_name]
    results={}
    for t_i in indices:
        score='%.2f'%models.sentiment_terms[t_i][0]['score']
        if "LABEL_0" in models.sentiment_terms[t_i][0]['label']:
            label="POSITIVE"
            sentiment = label+"_"+score
        elif "LABEL_1" in models.sentiment_terms[t_i][0]['label']:
            label="NEGATIVE"
            sentiment = label+"_"+score
        else:
           sentiment = models.sentiment_terms[t_i][0]['label']+"_"+score
        results[models.uris[t_i]]=[models.terms_info[t_i][1],models.terms_info[t_i][2], models.terms_info[t_i][4], models.terms_info[t_i][0], models.documents[t_i], sentiment]
    num_results=len(indices)
    first_topic=models.topics[indices[0]]
    fig1=models.topic_model.visualize_barchart([first_topic], n_words=10)
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


@query.route("/spelling_checker", methods=["GET", "POST"])
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
        index_uri=models.uris.index(uri_raw)
        definition=models.documents[index_uri]
        clean_definition=models.clean_documents[index_uri]
        results={}
        results[uri_raw]=[enum,year, vnum, term]
        return render_template('spelling_checker.html',results=results, clean_definition=clean_definition, definition=definition)


@query.route("/evolution_of_terms", methods=["GET", "POST"])
def evolution_of_terms(termlink=None):
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
        if "https://" in uri_checker or "w3id" in uri_checker:
            uri_raw=uri_checker.strip().replace("<","").replace(">","")
            uri="<"+uri_raw+">"
        elif uri_checker == "":
            uri_raw="https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0"
            uri="<"+uri_raw+">"
            print("uri %s!!" %uri)

    if not uri:
        print("not index uri!!")
        return render_template('evolution_of_terms.html')

    else:
        term, definition, enum, year, vnum  =get_document(uri)
        index_uri=models.uris.index(uri_raw)
        t_name=models.topics_names[index_uri]
        score='%.2f'%models.sentiment_terms[index_uri][0]['score']
        if "LABEL_0" in models.sentiment_terms[index_uri][0]['label']:
            label="POSITIVE"
            t_sentiment = label+"_"+score
        elif "LABEL_1" in models.sentiment_terms[index_uri][0]['label']:
            label="NEGATIVE"
            t_sentiment = label+"_"+score
        else:
            t_sentiment = models.sentiment_terms[index_uri][0]['label']+"_"+score

        print("----> index_uri in term evoultion is is %s" %index_uri)
        results_sim_first=retrieving_similariy(models.paraphrases_index_first, index_uri, models.paraphrases)
        results=[]
        topics_vis=[]
        r_similar_index=[]
        for r_sim in results_sim_first:
            rank, i, similar_index = r_sim
            r_similar_index.append(similar_index)
            print(similar_index)
            score='%.2f'%models.sentiment_terms[similar_index][0]['score']
            if "LABEL_0" in models.sentiment_terms[similar_index][0]['label']:
                label="POSITIVE"
                sentiment = label+"_"+score
            elif "LABEL_1" in models.sentiment_terms[similar_index][0]['label']:
                label="NEGATIVE"
                sentiment = label+"_"+score
            else:
                sentiment = models.sentiment_terms[similar_index][0]['label']+"_"+score
            topic_name = models.topics_names[similar_index]
            if models.topics[similar_index] not in topics_vis:
                topics_vis.append(models.topics[similar_index])
            results.append([models.uris[similar_index], models.terms_info[similar_index][1],models.terms_info[similar_index][2], models.terms_info[similar_index][4], models.terms_info[similar_index][0], models.documents[similar_index], topic_name, rank, sentiment])
        results_sim_second=retrieving_similariy(models.paraphrases_index_second, index_uri, models.paraphrases)
        for r_sim in results_sim_second:
            rank, similar_index, j = r_sim
            if similar_index not in r_similar_index:
                r_similar_index.append(similar_index)
                print(similar_index)
                score='%.2f'%models.sentiment_terms[similar_index][0]['score']
                if "LABEL_0" in models.sentiment_terms[similar_index][0]['label']:
                    label="POSITIVE"
                    sentiment = label+"_"+score
                elif "LABEL_1" in models.sentiment_terms[similar_index][0]['label']:
                    label="NEGATIVE"
                    sentiment = label+"_"+score
                else:
                    sentiment = models.sentiment_terms[similar_index][0]['label']+"_"+score
                topic_name = models.topics_names[similar_index]
                if models.topics[similar_index] not in topics_vis:
                    topics_vis.append(models.topics[similar_index])
                results.append([models.uris[similar_index], models.terms_info[similar_index][1],models.terms_info[similar_index][2], models.terms_info[similar_index][4], models.terms_info[similar_index][0], models.documents[similar_index], topic_name, rank, sentiment])

    results_sorted=[]
    results_sorted=sorted(results, key=itemgetter(2))
    results_dic_sorted={}
    for r in results_sorted:
        results_dic_sorted[r[0]]=r[1:]

    if len(topics_vis) >= 1:
        fig1=models.topic_model.visualize_barchart(topics_vis, n_words=10)
        bar_plot = fig1.to_json()
    else:
        bar_plot=None
    if len(topics_vis) >= 2:
        fig2=models.topic_model.visualize_heatmap(topics_vis)
        heatmap_plot = fig2.to_json()
    else:
        heatmap_plot=None

    return render_template('evolution_of_terms.html', results=results_dic_sorted,
                                term=term, definition=definition, uri=uri_raw,
                                enum=enum, year=year, vnum=vnum, t_name=t_name,
                                bar_plot=bar_plot, heatmap_plot=heatmap_plot, t_sentiment=t_sentiment)


@query.route("/defoe_queries", methods=["GET", "POST"])
def defoe_queries():
    defoe_q=dict_defoe_queries()

    if request.method == "POST":

        config={}
        defoe_selection=request.form.get('defoe_selection')
        print("defoe_selection is %s" %defoe_selection)
        config["preprocess"]=request.form.get('preprocess')
        config["target_sentences"]= request.form.get('target_sentences').split(",")
        config["target_filter"] = request.form.get('target_filter')
        config["window"] = request.form.get('window')
        config["defoe_path"]= "/Users/rf208/Research/NLS-Fellowship/work/defoe/"
        config["start_year"]= request.form.get('start_year')
        config["end_year"]= request.form.get('end_year')
        config["os_type"]="os"
        config["hit_count"] = request.form.get('hit_count')

        if "normalized" not in defoe_selection:
            file= request.files['file']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            config["data"]=os.path.join(app.config['UPLOAD_FOLDER'], filename)



        config_file=os.path.join(app.config['CONFIG_FOLDER'], "config_frances_web.yml")
        with open(config_file, 'w') as outfile:
            yaml.dump(config, outfile, default_flow_style=False)

        results_file=os.path.join(app.config['RESULTS_FOLDER'], defoe_selection+".yml")

        if "normalized" not in defoe_selection:
            print("spark-submit")
            cwd = os.getcwd()
            os.chdir(defoe_path)
            cmd="spark-submit --driver-memory 12g --py-files defoe.zip defoe/run_query.py sparql_data.txt sparql defoe.sparql.queries."+ defoe_selection+" "+ config_file  +" -r " + results_file +" -n 34"
            #os.system(cmd)
            os.chdir(cwd)

        print("finished with apache sark submission, results in -- %s" % results_file)
        results=read_results(results_file)

        #### creating config_defoe ####
        config_defoe={}
        if "terms" in defoe_selection or "uris" in defoe_selection:
            config_defoe["preprocess"]= config["preprocess"]
            config_defoe["target_sentences"]= config["target_sentences"]
            config_defoe["target_filter"] = config["target_filter"]
            config_defoe["start_year"]= config["start_year"]
            config_defoe["end_year"]= config["end_year"]
            if "snippet" in defoe_selection:
                config_defoe["window"] = config["window"]
        elif "frequency" in defoe_selection:
            config_defoe["preprocess"]= config["preprocess"]
            config_defoe["target_sentences"]= config["target_sentences"]
            config_defoe["target_filter"] = config["target_filter"]
            config_defoe["start_year"]= config["start_year"]
            config_defoe["end_year"]= config["end_year"]
            config_defoe["hit_count"] = config["hit_count"]



        if "terms" in defoe_selection:
            results_uris=results["terms_uris"]
            print("Sending results")
            return render_template('defoe_results.html', defoe_q=defoe_q, flag=1, results=results, results_uris=results_uris,  defoe_selection=defoe_selection, config=config_defoe)

        elif "uris" in defoe_selection or "normalized" in defoe_selection:

            print("Sending results")
            return render_template('defoe_results.html', defoe_q=defoe_q, flag=1, results=results, defoe_selection=defoe_selection, config=config_defoe)
        else:
            preprocess= request.args.get('preprocess', None)
            p_lexicon = preprocess_lexicon(config["data"], config["preprocess"])

            #### Read Normalized data
            norm_file=os.path.join(app.config['RESULTS_FOLDER'], "publication_normalized.yml")
            ####
            norm_publication=read_results(norm_file)
            taxonomy=p_lexicon
            plot_f, plot_n_f=plot_taxonomy_freq(taxonomy, results, norm_publication)
            #### only for ploty figures
            line_f_plot = plot_f.to_json()
            line_n_f_plot = plot_n_f.to_json()
            ####
            print("Sending results")
            return render_template('defoe_results.html', defoe_q=defoe_q, flag=1, results=results, defoe_selection=defoe_selection, line_f_plot=line_f_plot, line_n_f_plot=line_n_f_plot, config=config_defoe)

    return render_template('defoe.html', defoe_q=defoe_q)

@query.route("/download", methods=['GET'])
def download(defoe_selection=None):
    defoe_selection = request.args.get('defoe_selection', None)
    cwd = os.getcwd()
    os.chdir(app.config['RESULTS_FOLDER'])
    results_file=defoe_selection+".yml"
    zip_file = defoe_selection+".zip"
    with ZipFile(zip_file, 'w') as zipf:
        zipf.write(results_file)
    os.chdir(cwd)
    zip_file=os.path.join(app.config['RESULTS_FOLDER'], zip_file)
    return send_file(zip_file, as_attachment=True)

@query.route("/visualize_freq", methods=['GET'])
def visualize_freq(defoe_selection=None):
    defoe_selection = request.args.get('defoe_selection', None)
    lexicon_file = request.args.get('lexicon_file', None)
    results_file=os.path.join(app.config['RESULTS_FOLDER'], defoe_selection+".yml")

    preprocess= request.args.get('preprocess', None)
    p_lexicon = preprocess_lexicon(lexicon_file, preprocess)
    defoe_q=dict_defoe_queries()

    #### Read Results File
    results=read_results(results_file)



    #### Read Normalized data
    norm_file=os.path.join(app.config['RESULTS_FOLDER'], "publication_normalized.yml")
    ####
    norm_publication=read_results(norm_file)
    print("---%s---" %norm_publication)
    taxonomy=p_lexicon
    plot_f, plot_n_f=plot_taxonomy_freq(taxonomy, results, norm_publication)
    #### only for ploty figures
    line_f_plot = plot_f.to_json()
    line_n_f_plot = plot_n_f.to_json()
    ####
    return render_template('defoe.html', defoe_q=defoe_q, flag=1, results=results, defoe_selection=defoe_selection, lexicon_file=lexicon_file, line_f_plot=line_f_plot, line_n_f_plot=line_n_f_plot)
