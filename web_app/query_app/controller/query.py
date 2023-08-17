import io

from flask import Blueprint, send_file, request, jsonify, session, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_paginate import Pagination
from http import HTTPStatus

from .sparql_queries import *
from itertools import islice

from .utils import calculating_similarity_text, get_topic_name, retrieving_similariy
from .utils import dict_defoe_queries, read_results, get_kg_type, get_kg_url
from .utils import pagination_to_dict, sanitize_results, figure_to_dict

import time, os, yaml
from zipfile import *
from operator import itemgetter

from werkzeug.utils import secure_filename

from ..core import limiter
from flasgger import swag_from

from ..db import DefoeQueryConfig, DefoeQueryTask
from web_app.query_app.flask_config import DefaultFlaskConfig
from .models import ModelsRepository

query = Blueprint("query", __name__, url_prefix="/api/v1/query")
query_protected = Blueprint("query_protected", __name__, url_prefix="/api/v1/protected/query")
database = DefaultFlaskConfig.DATABASE
models = ModelsRepository
defoe_service = DefaultFlaskConfig.DEFOE_SERVICE
upload_folder = DefaultFlaskConfig.UPLOAD_FOLDER
result_folder = DefaultFlaskConfig.RESULTS_FOLDER
google_cloud_storage = DefaultFlaskConfig.GOOGLE_CLOUD_STORAGE


@query.route("/term_search/<string:termlink>", methods=['GET'])
@query.route("/term_search", methods=['POST'])
@swag_from("../docs/query/term_search.yml")
@limiter.limit("30/minute")  # 30 requests per minute
def term_search(termlink=None):
    if request.method == "POST":
        term = request.json.get("search")
        if term == "":
            term = "AABAM"
        term = term.upper()
        session['term'] = term

    if termlink != None:
        term = termlink
        session['term'] = term
    else:
        term = session.get('term')

    headers = ["Year", "Edition", "Volume", "Start Page", "End Page", "Term Type", "Definition/Summary",
               "Related Terms", "Topic Modelling", "Sentiment_Score", "Advanced Options"]

    results = get_definition(term, models.documents, models.uris)
    topics_vis = []
    for key, value in results.items():
        try:
            index_uri = models.uris.index(key)
            topic_name = models.topics_names[index_uri]
            score = '%.2f' % models.sentiment_terms[index_uri][0]['score']
            if "LABEL_0" in models.sentiment_terms[index_uri][0]['label']:
                label = "POSITIVE"
                sentiment = label + "_" + score
            elif "LABEL_1" in models.sentiment_terms[index_uri][0]['label']:
                label = "NEGATIVE"
                sentiment = label + "_" + score
            else:
                sentiment = models.sentiment_terms[index_uri][0]['label'] + "_" + score
            if models.topics[index_uri] not in topics_vis:
                topics_vis.append(models.topics[index_uri])
            topic_name = get_topic_name(index_uri, models.topics, models.topic_model)
            topic_name = topic_name.replace(" ", "_")
            print("---- topic_name is %s" % topic_name)
            value.append(topic_name)
            value.append(sentiment)
            value.append(key)
        except:
            pass
    if len(topics_vis) >= 1:
        bar_plot = models.topic_model.visualize_barchart(topics_vis, n_words=10)
    else:
        bar_plot = None
    if len(topics_vis) >= 2:
        heatmap_plot = models.topic_model.visualize_heatmap(topics_vis)
    else:
        heatmap_plot = None

    page = int(request.json.get("page", 1))
    page_size = 2
    per_page = 2
    offset = (page - 1) * per_page
    limit = offset + per_page
    results_for_render = dict(islice(results.items(), offset, limit))
    pagination = Pagination(page=page, total=len(results), per_page=page_size, search=False)

    return jsonify({
        "results": results_for_render,
        "pagination": pagination_to_dict(pagination),
        "headers": headers,
        "term": term,
        "bar_plot": figure_to_dict(bar_plot),
        "heatmap_plot": figure_to_dict(heatmap_plot),
    }), HTTPStatus.OK


@query.route("/visualization_resources", methods=['POST'])
@swag_from("../docs/query/visualization_resources.yml")
@limiter.limit("30/minute")  # 30 requests per minute
def visualization_resources():
    if 'resource_uri' in request.json and 'collection' in request.json:
        uri_raw = request.json.get('resource_uri').strip().replace("<", "").replace(">", "")
        collection = request.json.get('collection')
        kg_type = get_kg_type(collection)
        if uri_raw == "":
            uri = "<https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0>"
        else:
            uri = "<" + uri_raw + ">"
        g_results = describe_resource(uri, kg_type)
        return jsonify({
            "results": g_results,
            "uri": uri,
        }), HTTPStatus.OK

    # return error status code
    return jsonify({
        "message": "termlink not found",
    }), HTTPStatus.BAD_REQUEST


@query.route("/similar_terms", methods=["GET", "POST"])
@swag_from("../docs/query/similar_terms.yml")
@limiter.limit("30/minute")  # 30 requests per minute
def similar_terms(termlink=None):
    uri = ""
    uri_raw = ""
    data_similar = ""
    topics_vis = []
    termlink = request.args.get('termlink', None)
    termtype = request.args.get('termtype', None)
    if termlink != None:
        if ">" in termlink:
            termlink = termlink.split(">")[0]
        uri = "<https://w3id.org/eb/i/" + termtype + "/" + termlink + ">"
        uri_raw = uri.replace("<", "").replace(">", "")
        session['uri_raw'] = uri_raw
        session['uri'] = uri
        session["data_similar"] = ""

    elif 'resource_uri' in request.json:
        data_similar = request.json.get('resource_uri')
        if "https://" in data_similar or "w3id" in data_similar:
            uri_raw = data_similar.strip().replace("<", "").replace(">", "")
        elif data_similar == "":
            uri_raw = "https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0"
        else:
            uri_raw = ""
            session['uri_raw'] = "free_search"
        if uri_raw != "":
            uri = "<" + uri_raw + ">"
            session['uri_raw'] = uri_raw
        session['uri'] = uri
        session["data_similar"] = data_similar

    if not uri:
        uri = session.get('uri')
        uri_raw = session.get('uri_raw')
        data_similar = session.get('data_similar')

    if "free_search" in uri_raw:
        results, topics_vis = calculating_similarity_text(data_similar, models.text_embeddings, models.model,
                                                          models.terms_info, models.documents, models.uris,
                                                          models.topics_names, models.topics, models.sentiment_terms,
                                                          -1)

    else:
        term, definition, enum, year, vnum = get_document(uri)
        index_uri = models.uris.index(uri_raw)
        t_name = models.topics_names[index_uri]
        score = '%.2f' % models.sentiment_terms[index_uri][0]['score']
        if "LABEL_0" in models.sentiment_terms[index_uri][0]['label']:
            label = "POSITIVE"
            t_sentiment = label + "_" + score
        elif "LABEL_1" in models.sentiment_terms[index_uri][0]['label']:
            label = "NEGATIVE"
            t_sentiment = label + "_" + score
        else:
            t_sentiment = models.sentiment_terms[index_uri][0]['label'] + "_" + score

        print("----> index_uri is %s" % index_uri)
        results = {}
        # results_sim_first=retrieving_similariy(paraphrases_index_first, index_uri, paraphrases)
        # r_similar_index=[]
        # for r_sim in results_sim_first:
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
        # results_sim_second=retrieving_similariy(paraphrases_index_second, index_uri, paraphrases)
        # for r_sim in results_sim_second:
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
        # if len(r_similar_index)==0:
        results, topics_vis = calculating_similarity_text(definition, models.text_embeddings, models.model,
                                                          models.terms_info, models.documents, models.uris,
                                                          models.topics_names, models.topics, models.sentiment_terms,
                                                          index_uri)
    if len(topics_vis) >= 1:
        bar_plot = models.topic_model.visualize_barchart(topics_vis, n_words=10)
    if len(topics_vis) >= 1:
        bar_plot = models.topic_model.visualize_barchart(topics_vis, n_words=10)
    else:
        bar_plot = None
    if len(topics_vis) >= 2:
        heatmap_plot = models.topic_model.visualize_heatmap(topics_vis)
    else:
        heatmap_plot = None

    #### Pagination ###
    page = int(request.json.get("page", 1))
    page_size = 10
    per_page = 10
    offset = (page - 1) * per_page
    limit = offset + per_page
    results_page = dict(islice(results.items(), offset, limit))
    results_for_render = sanitize_results(results_page)
    pagination = Pagination(page=page, total=len(results), per_page=page_size, search=False)
    ##############

    if "free_search" in uri_raw:
        return jsonify({
            "results": results_for_render,
            "pagination": pagination_to_dict(pagination),
            "bar_plot": figure_to_dict(bar_plot),
            "heatmap_plot": figure_to_dict(heatmap_plot),
        }), HTTPStatus.OK
    else:
        return jsonify({
            "results": results_for_render,
            "pagination": pagination_to_dict(pagination),
            "term": term,
            "definition": definition,
            "uri": uri_raw,
            "enum": enum,
            "year": year,
            "vnum": vnum,
            "topicName": t_name,
            "topicSentiment": t_sentiment,
            "bar_plot": figure_to_dict(bar_plot),
            "heatmap_plot": figure_to_dict(heatmap_plot),
        }), HTTPStatus.OK


@query.route("/topic_modelling", methods=["GET", "POST"])
@swag_from("../docs/query/topic_modelling.yml")
@limiter.limit("30/minute")  # 30 requests per minute
def topic_modelling(topic_name=None):
    topic_name = request.args.get('topic_name', None)
    num_topics = len(models.t_names) - 2
    if topic_name == None:
        if 'topic_name' in request.json:
            topic_name = request.json.get('topic_name')
            if topic_name == "":
                topic_name = "0_hindustan_of_hindustan_hindustan_in_district"
            else:
                if topic_name not in models.t_names:
                    full_topic_name = ""
                    number = topic_name + "_"
                    for x in models.t_names:
                        if x.startswith(number):
                            full_topic_name = x
                    if full_topic_name:
                        topic_name = full_topic_name
                    else:
                        topic_name = "0_hindustan_of_hindustan_hindustan_in_district"
            session['topic_name'] = topic_name

    if not topic_name:
        topic_name = session.get('topic_name')
    if not topic_name:
        return jsonify({
            "num_topics": num_topics,
        }), HTTPStatus.OK

    indices = [i for i, x in enumerate(models.topics_names) if x == topic_name]
    results = {}
    for t_i in indices:
        score = '%.2f' % models.sentiment_terms[t_i][0]['score']
        if "LABEL_0" in models.sentiment_terms[t_i][0]['label']:
            label = "POSITIVE"
            sentiment = label + "_" + score
        elif "LABEL_1" in models.sentiment_terms[t_i][0]['label']:
            label = "NEGATIVE"
            sentiment = label + "_" + score
        else:
            sentiment = models.sentiment_terms[t_i][0]['label'] + "_" + score
        results[models.uris[t_i]] = [models.terms_info[t_i][1], models.terms_info[t_i][2], models.terms_info[t_i][4],
                                     models.terms_info[t_i][0], models.documents[t_i], sentiment]
    num_results = len(indices)
    first_topic = models.topics[indices[0]]
    bar_plot = models.topic_model.visualize_barchart([first_topic], n_words=10)

    #### Pagination ###
    page = int(request.json.get("page", 1))
    page_size = 10
    per_page = 10
    offset = (page - 1) * per_page
    limit = offset + per_page
    results_page = dict(islice(results.items(), offset, limit))
    results_for_render = sanitize_results(results_page)
    pagination = Pagination(page=page, total=len(results), per_page=page_size, search=False)
    ##############

    return jsonify({
        "topic_name": topic_name,
        "results": results_for_render,
        "pagination": pagination_to_dict(pagination),
        "bar_plot": figure_to_dict(bar_plot),
        "num_results": num_results,
        "num_topics": num_topics,
    }), HTTPStatus.OK


@query.route("/spelling_checker", methods=["GET", "POST"])
@swag_from("../docs/query/spelling_checker.yml")
@limiter.limit("30/minute")  # 30 requests per minute
def spelling_checker(termlink=None):
    uri_raw = ""
    uri = ""
    termlink = request.args.get('termlink', None)
    termtype = request.args.get('termtype', None)
    if termlink != None:
        if ">" in termlink:
            termlink = termlink.split(">")[0]
        uri = "<https://w3id.org/eb/i/" + termtype + "/" + termlink + ">"
        uri_raw = uri.replace("<", "").replace(">", "")

    elif 'resource_uri' in request.json:
        uri_checker = request.json.get('resource_uri')
        if "https://" in uri_checker or "w3id" in uri_checker:
            uri_raw = uri_checker.strip().replace("<", "").replace(">", "")
            uri = "<" + uri_raw + ">"
        elif uri_checker == "":
            uri_raw = "https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0"
            uri = "<" + uri_raw + ">"

    if not uri:
        return jsonify({
            "message": "no term given"
        }), HTTPStatus.BAD_REQUEST
    else:
        term, definition, enum, year, vnum = get_document(uri)
        index_uri = models.uris.index(uri_raw)
        definition = models.documents[index_uri]
        clean_definition = models.clean_documents[index_uri]
        results = {}
        results[uri_raw] = [enum, year, vnum, term]
        return jsonify({
            "results": results,
            "clean_definition": clean_definition,
            "definition": definition,
        }), HTTPStatus.OK


@query.route("/evolution_of_terms", methods=["GET", "POST"])
@swag_from("../docs/query/evolution_of_terms.yml")
def evolution_of_terms(termlink=None):
    uri_raw = ""
    uri = ""
    termlink = request.args.get('termlink', None)
    termtype = request.args.get('termtype', None)
    if termlink != None:
        if ">" in termlink:
            termlink = termlink.split(">")[0]
        uri = "<https://w3id.org/eb/i/" + termtype + "/" + termlink + ">"
        uri_raw = uri.replace("<", "").replace(">", "")

    elif 'resource_uri' in request.json:
        uri_checker = request.json.get('resource_uri')
        if "https://" in uri_checker or "w3id" in uri_checker:
            uri_raw = uri_checker.strip().replace("<", "").replace(">", "")
            uri = "<" + uri_raw + ">"
        elif uri_checker == "":
            uri_raw = "https://w3id.org/eb/i/Article/992277653804341_144133901_AABAM_0"
            uri = "<" + uri_raw + ">"
            print("uri %s!!" % uri)

    if not uri:
        return jsonify({
            "message": "no term given"
        }), HTTPStatus.BAD_REQUEST

    else:
        term, definition, enum, year, vnum = get_document(uri)
        index_uri = models.uris.index(uri_raw)
        t_name = models.topics_names[index_uri]
        score = '%.2f' % models.sentiment_terms[index_uri][0]['score']
        if "LABEL_0" in models.sentiment_terms[index_uri][0]['label']:
            label = "POSITIVE"
            t_sentiment = label + "_" + score
        elif "LABEL_1" in models.sentiment_terms[index_uri][0]['label']:
            label = "NEGATIVE"
            t_sentiment = label + "_" + score
        else:
            t_sentiment = models.sentiment_terms[index_uri][0]['label'] + "_" + score

        print("----> index_uri in term evoultion is is %s" % index_uri)
        results_sim_first = retrieving_similariy(models.paraphrases_index_first, index_uri, models.paraphrases)
        results = []
        topics_vis = []
        r_similar_index = []
        for r_sim in results_sim_first:
            rank, i, similar_index = r_sim
            r_similar_index.append(similar_index)
            print(similar_index)
            score = '%.2f' % models.sentiment_terms[similar_index][0]['score']
            if "LABEL_0" in models.sentiment_terms[similar_index][0]['label']:
                label = "POSITIVE"
                sentiment = label + "_" + score
            elif "LABEL_1" in models.sentiment_terms[similar_index][0]['label']:
                label = "NEGATIVE"
                sentiment = label + "_" + score
            else:
                sentiment = models.sentiment_terms[similar_index][0]['label'] + "_" + score
            topic_name = models.topics_names[similar_index]
            if models.topics[similar_index] not in topics_vis:
                topics_vis.append(models.topics[similar_index])
            results.append(
                [models.uris[similar_index], models.terms_info[similar_index][1], models.terms_info[similar_index][2],
                 models.terms_info[similar_index][4], models.terms_info[similar_index][0],
                 models.documents[similar_index], topic_name, rank, sentiment])
        results_sim_second = retrieving_similariy(models.paraphrases_index_second, index_uri, models.paraphrases)
        for r_sim in results_sim_second:
            rank, similar_index, j = r_sim
            if similar_index not in r_similar_index:
                r_similar_index.append(similar_index)
                print(similar_index)
                score = '%.2f' % models.sentiment_terms[similar_index][0]['score']
                if "LABEL_0" in models.sentiment_terms[similar_index][0]['label']:
                    label = "POSITIVE"
                    sentiment = label + "_" + score
                elif "LABEL_1" in models.sentiment_terms[similar_index][0]['label']:
                    label = "NEGATIVE"
                    sentiment = label + "_" + score
                else:
                    sentiment = models.sentiment_terms[similar_index][0]['label'] + "_" + score
                topic_name = models.topics_names[similar_index]
                if models.topics[similar_index] not in topics_vis:
                    topics_vis.append(models.topics[similar_index])
                results.append([models.uris[similar_index], models.terms_info[similar_index][1],
                                models.terms_info[similar_index][2], models.terms_info[similar_index][4],
                                models.terms_info[similar_index][0], models.documents[similar_index], topic_name, rank,
                                sentiment])

    results_sorted = []
    results_sorted = sorted(results, key=itemgetter(2))
    results_dic_sorted = {}
    for r in results_sorted:
        results_dic_sorted[r[0]] = r[1:]

    if len(topics_vis) >= 1:
        bar_plot = models.topic_model.visualize_barchart(topics_vis, n_words=10)
    else:
        bar_plot = None
    if len(topics_vis) >= 2:
        heatmap_plot = models.topic_model.visualize_heatmap(topics_vis)
    else:
        heatmap_plot = None

    return jsonify({
        "results": sanitize_results(results_dic_sorted),
        "term": term,
        "definition": definition,
        "uri": uri_raw,
        "enum": enum,
        "year": year,
        "vnum": vnum,
        "topicName": t_name,
        "bar_plot": figure_to_dict(bar_plot),
        "heatmap_plot": figure_to_dict(heatmap_plot),
        "topicSentiment": t_sentiment,
    }), HTTPStatus.OK


def create_defoe_query_config(kg_type, preprocess, hit_count, data_file,
                              target_sentences, target_filter, start_year, end_year,
                              window, gazetteer, bounding_box):
    config = {}
    if kg_type:
        config["kg_type"] = kg_type

    if preprocess:
        config["preprocess"] = preprocess

    if hit_count:
        config["hit_count"] = hit_count

    if data_file:
        config["data"] = data_file

    if target_sentences:
        config["target_sentences"] = target_sentences

    if target_filter:
        config["target_filter"] = target_filter

    if start_year:
        # start_year from request is integer, while defoe need string
        config["start_year"] = str(start_year)

    if end_year:
        # end_year from request is integer, while defoe need string
        config["end_year"] = str(end_year)

    if window:
        # end_year from request is integer, while defoe need string
        config["window"] = str(window)

    if gazetteer:
        config["gazetteer"] = gazetteer

    if bounding_box:
        config["bounding_box"] = bounding_box

    return config


@query_protected.route("/defoe_submit", methods=["POST"])
@swag_from("../docs/query/defoe_submit.yml")
@jwt_required()
@limiter.limit("2/minute")  # 2 requests per minute
def defoe_queries():
    user_id = get_jwt_identity()

    defoe_selection = request.json.get('defoe_selection')

    # build defoe config from request
    preprocess = request.json.get('preprocess')
    target_sentences = request.json.get('target_sentences')
    target_filter = request.json.get('target_filter')
    start_year = request.json.get('start_year')
    end_year = request.json.get('end_year')
    hit_count = request.json.get('hit_count')
    lexicon_file = request.json.get('file', '')
    data_file = os.path.join(upload_folder, user_id, lexicon_file)

    # For geoparser_by_year query, add bounding_box and gazetteer
    bounding_box = request.json.get('bounding_box')
    gazetteer = request.json.get('gazetteer')
    collection = request.json.get('collection', 'Encyclopaedia Britannica')

    kg_type = get_kg_type(collection)

    # For terms_snippet_keysearch_by_year query, add window
    window = request.json.get('window')

    # Save config data to database
    defoe_query_config = DefoeQueryConfig.create_new(collection, defoe_selection, preprocess, lexicon_file,
                                                     target_sentences, target_filter,
                                                     start_year, end_year, hit_count,
                                                     window, gazetteer, bounding_box)
    database.add_defoe_query_config(defoe_query_config)

    # Save defoe query task information to database

    query_task = DefoeQueryTask.create_new(user_id, defoe_query_config, "", "")
    result_filename = str(query_task.id) + ".yml"
    result_file_path = os.path.join(result_folder, user_id, str(query_task.id) + ".yml")

    if (kg_type + '_' + defoe_selection) in defoe_service.get_pre_computed_queries():
        result_file_path = defoe_service.get_pre_computed_queries()[kg_type + '_' + defoe_selection]
        result_filename = result_file_path

    query_task.resultFile = result_filename

    # create query_config for defoe query
    config = create_defoe_query_config(kg_type, preprocess, hit_count, data_file,
                                       target_sentences, target_filter, start_year, end_year, window,
                                       gazetteer, bounding_box)

    try:
        # Submit defoe query task
        defoe_service.submit_job(
            job_id=str(query_task.id),
            model_name="sparql",
            query_name=defoe_selection,
            endpoint=get_kg_url(kg_type),
            query_config=config,
            result_file_path=result_file_path
        )
        database.add_defoe_query_task(query_task)

        return jsonify({
            "success": True,
            "id": query_task.id,
        })
    except Exception as e:
        current_app.logger.info(e)
        return jsonify({
            "success": False
        })


@query_protected.route("/defoe_cancel", methods=["POST"])
@jwt_required()
def cancel_defoe_query():
    user_id = get_jwt_identity()
    task_id = request.json.get("id")
    task = database.get_defoe_query_task_by_taskID(task_id, user_id)

    if task is None:
        # No such defoe query task
        return jsonify({
            "success": False,
            "error": "No such task!"
        })

    if task.state != 'PENDING' and task.state != 'RUNNING':
        # Task has been finished, can not be cancelled
        return jsonify({
            "success": False,
            "error": "Current state: %s, Task can only be cancelled when it is pending or running!" % task.state
        })

    try:
        defoe_service.cancel_job(task_id)
        return jsonify({
            "success": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@query_protected.route("/upload", methods=["POST"])
@swag_from("../docs/query/upload.yml")
@jwt_required()
@limiter.limit("2/second")  # 2 requests per second
def upload():
    user_id = get_jwt_identity()
    user_folder = os.path.join(upload_folder, user_id)
    # Make directories relative to the working folder
    os.makedirs(user_folder, exist_ok=True)
    file = request.files['file']
    submit_name = secure_filename(file.filename)
    save_name = time.strftime("%Y%m%d-%H%M%S") + "_" + submit_name
    source_file_path = os.path.join(user_folder, save_name)
    print(source_file_path)
    file.save(source_file_path)

    if current_app.config["FILE_STORAGE_MODE"] == "gs":
        # Upload it to Google Cloud Storage
        # It will look from the relative path from the working folder
        google_cloud_storage.upload_blob_from_filename(source_file_path, source_file_path)

    return jsonify({
        "success": True,
        "file": save_name,
    })


@query.route("/defoe_list", methods=["GET"])
@swag_from("../docs/query/defoe_list.yml")
def defoe_list():
    return jsonify({
        "queries": list(dict_defoe_queries().keys()),
    })


@query_protected.route("/defoe_status", methods=["POST"])
@swag_from("../docs/query/defoe_status.yml")
@jwt_required()
def defoe_status():
    user_id = get_jwt_identity()
    task_id = request.json.get("id")
    # Validate task_id
    # If the task exits
    # If the task is accessible to this user
    current_app.logger.info('defoe_status')
    current_app.logger.info('task_id: %s', task_id)

    try:
        task = database.get_defoe_query_task_by_taskID(task_id, user_id)

        # When query job is done
        if task.state == "DONE":
            return jsonify({
                "id": task_id,
                "results": task.resultFile,
                "state": task.state,
                "progress": task.progress
            })
        if task.state == "ERROR":
            return jsonify({
                "id": task_id,
                "state": "ERROR",
                "error": task.errorMsg,
                "progress": task.progress
            })

        if task.state == "CANCELLED":
            return jsonify({
                "id": task_id,
                "state": task.state,
                "progress": task.progress
            })

        # When query job is not done

        status = defoe_service.get_status(task_id)
        state = status["state"]
        output = {
            "id": task_id,
        }

        if state == "DONE":
            task.progress = 100
            output["results"] = task.resultFile

        elif state == "SETUP_DONE":
            task.progress = 5

        elif state == "RUNNING":
            task.progress = 10

        elif state == "ERROR":
            task.progress = 100
            output["error"] = status["details"]

        elif state == "CANCELLED":
            task.progress = 100

        if state != task.state:
            task.state = state
            database.update_defoe_query_task(task)

        output["state"] = task.state
        output["progress"] = task.progress

        return jsonify(output)

    except Exception as E:
        print(E)
        return jsonify({
            'error': 'Job does not exist!'
        }, HTTPStatus.BAD_REQUEST)


@query_protected.route("/defoe_query_task", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def defoe_query_task():
    user_id = get_jwt_identity()
    task_id = request.json.get('task_id')
    # Validate task_id
    # If this task exists
    task = database.get_defoe_query_task_by_taskID(task_id, user_id)
    if task is None:
        return jsonify({
            "error": 'This Defoe Query Task does not exist!'
        }), HTTPStatus.BAD_REQUEST
    else:
        if task.config.queryType == "frequency_keysearch_by_year":
            kg_type = get_kg_type(task.config.collection)
            query_info = kg_type + "_publication_normalized"
            return jsonify({
                "task": task.to_dict(),
                "publication_normalized_result_path": defoe_service.get_pre_computed_queries()[query_info]
            }), HTTPStatus.OK
        return jsonify({
            "task": task.to_dict()
        }), HTTPStatus.OK


def result_filename_to_absolute_filepath(result_filename, user_id):
    if "precomputedResult" in result_filename:
        if current_app.config["FILE_STORAGE_MODE"] == "gs":
            return result_filename
        base_dir = str(current_app.config['BASE_DIR'])
        print(base_dir)
        print(os.path.join(base_dir, result_filename))
        return os.path.join(base_dir, result_filename)
    return os.path.join(result_folder, user_id, result_filename)


@query_protected.route("/defoe_query_result", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def defoe_query_result():
    user_id = get_jwt_identity()
    result_filename = request.json.get('result_filename')
    result_filepath = result_filename_to_absolute_filepath(result_filename, user_id)
    print(result_filepath)
    if current_app.config["FILE_STORAGE_MODE"] == "gs":
        # Validate file path
        # If the file exists
        # TODO If the file is accessible to this user
        # Convert result to object
        results = google_cloud_storage.read_results(result_filepath)
        return jsonify({
            "results": results
        })

    if current_app.config["FILE_STORAGE_MODE"] == "local":
        # Validate file path
        # If the file exists
        if result_filepath is not None and not os.path.isfile(result_filepath):
            print("file does not exist!")
            return jsonify({
                "error": 'File does not exist!'
            }), HTTPStatus.BAD_REQUEST
        # TODO If the file is accessible to this user
        # Convert result to object
        results = read_results(result_filepath)
        return jsonify({
            "results": results
        })


@query_protected.route("/defoe_query_tasks", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def defoe_query_tasks():
    user_id = get_jwt_identity()
    print('query')
    # List all defoe query tasks this user submitted
    tasks = database.get_all_defoe_query_tasks_by_userID(user_id)

    return jsonify({
        "tasks": list(map(lambda task: task.to_dict(), tasks))
    })


@query_protected.route("/download", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def download():
    user_id = get_jwt_identity()
    result_filename = request.json.get('result_filename', None)
    print(result_filename)

    result_file_path = result_filename_to_absolute_filepath(result_filename, user_id)
    print(result_file_path)
    zip_file_path = result_file_path[:-3] + "zip"

    if current_app.config["FILE_STORAGE_MODE"] == "gs":
        result_user_folder = os.path.dirname(result_file_path)
        print(result_user_folder)
        # Make directories relative to the working folder
        os.makedirs(result_user_folder, exist_ok=True)
        print(os.path.basename(result_filename))

        # It will download file to result_filename, which tells the relative path from the working folder
        google_cloud_storage.download_blob_from_filename(result_file_path, result_file_path)
        with ZipFile(zip_file_path, 'w', ZIP_DEFLATED) as zipf:
            zipf.write(result_filename, arcname=os.path.basename(result_filename))
    elif current_app.config["FILE_STORAGE_MODE"] == "local":
        print(zip_file_path)
        with ZipFile(zip_file_path, 'w', ZIP_DEFLATED) as zipf:
            zipf.write(result_file_path, arcname=os.path.basename(result_file_path))
    # send_file function will look for the absolute path of a file.
    return send_file(os.path.abspath(zip_file_path), as_attachment=True)
