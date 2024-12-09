from http import HTTPStatus

from flask import Blueprint, request, jsonify, current_app
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

from ..core import limiter
from ..service import search_service
from . import sparql_queries
from .utils import normalize_text, get_word_frequencies

search = Blueprint("search", __name__, url_prefix="/api/v1/search")


@search.get("/")
@limiter.limit("30/minute")  # 30 requests per minute
def text_search():
    # Construct the query dictionary from request arguments
    size = request.args.get('perPage', 10, type=int)
    exact_match = True if request.args.get('exact_match') == 'true' else False
    phrase_match = True if request.args.get('phrase_match') == 'true' else False
    query_params = {
        'search_type': request.args.get('search_type', 'lexical'),
        'keyword': request.args.get('keyword', ''),
        'search_field': request.args.get('search_field', 'full_text'),
        'exact_match': exact_match,
        'phrase_match': phrase_match,
        'sort': request.args.get('sort', "_score"),
        'order': request.args.get('order', "desc"),
        'from': (request.args.get('page', 1, type=int) - 1) * size,
        'size': size,
    }
    print(query_params)

    # Optional: handling range filters for year_published
    year_published_range_gte = request.args.get('year_published_range_gte', type=int)
    year_published_range_lte = request.args.get('year_published_range_lte', type=int)
    if year_published_range_gte or year_published_range_lte:
        query_params['year_published_range'] = {
            'gte': year_published_range_gte,
            'lte': year_published_range_lte
        }

    # Optional: handling filters for collection, genre, print_location
    for field in ["collection", "genre", "print_location", "edition_name"]:
        if value := request.args.get(field, None):
            query_params[field] = value

    if query_params["search_field"] == "term_name" or query_params["search_field"] == "vol_title":
        query_params["search_field"] = 'name'

    # Call the search service with the constructed query dictionary
    current_app.logger.info(f"search with options: {query_params}")
    try:
        #print(query_params)
        results = search_service.search(query_params)
        return jsonify(results.body), HTTPStatus.OK
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@search.get("/term")
@limiter.limit("30/minute")  # 30 requests per minute
def retrieve_term_info():
    term_path = request.args.get('term_path', type=str)
    term_uri = "https://w3id.org/hto/" + term_path
    current_app.logger.info(f"retrieve term info for {term_uri}")
    #print(term_path)
    term_info = sparql_queries.get_term_info(term_uri)
    es_term_info = search_service.get_term_info(term_uri)
    term_info["concept_uri"] = es_term_info["concept_uri"]
    term_info["alter_names"] = es_term_info["alter_names"]
    term_info["reference_terms"] = es_term_info["reference_terms"]
    term_info["supplements_to"] = es_term_info["supplements_to"]
    if "sentiment" in es_term_info:
        term_info["sentiment"] = es_term_info["sentiment"]
    return jsonify(term_info), HTTPStatus.OK


@search.post("/similar_terms")
@limiter.limit("30/minute")  # 30 requests per minute
def retrieve_similar_terms():
    term_uri = request.json.get("term_uri")
    #print(term_uri)
    term_info = search_service.get_term_info(term_uri)
    # get the top 20 most similar terms, expect itself.
    query = {
        "query_embedding": term_info["embedding"],
        "from": 1,
        "size": 21
    }
    threshold = 0.6
    knn_search_response = search_service.exact_knn_search(query)
    similar_terms = knn_search_response.body["hits"]["hits"]
    similar_terms_list = []
    for similar_term in similar_terms:
        if similar_term["_score"] > threshold:
            similar_terms_list.append({
                "uri": similar_term["_id"],
                "name": similar_term["_source"]["name"],
                "year": similar_term["_source"]["year_published"]
            })
    return jsonify(similar_terms_list), HTTPStatus.OK


@search.get("/page_display")
@limiter.limit("30/minute")  # 30 requests per minute
def retrieve_page_display_info():
    page_path = request.args.get('page_path', type=str)
    page_uri = "<https://w3id.org/hto/" + page_path + ">"
    #print(page_path)
    page_info = sparql_queries.get_page_display_info(page_uri)
    return jsonify(page_info), HTTPStatus.OK


@search.get("/page")
@limiter.limit("30/minute")  # 30 requests per minute
def retrieve_page_info():
    page_path = request.args.get('page_path', type=str)
    page_uri = "<https://w3id.org/hto/" + page_path + ">"
    current_app.logger.info(f"retrieve page info for {page_uri}")
    #print(page_path)
    page_info = sparql_queries.get_page_info(page_uri)
    return jsonify(page_info), HTTPStatus.OK


@search.post("/similar_term_descriptions")
@limiter.limit("30/minute")  # 30 requests per minute
def retrieve_similar_term_descriptions():
    term_uri = request.json.get("term_uri")
    #print(term_uri)
    term_info = search_service.get_term_info(term_uri)

    # get the top 20 most similar terms, since we want itself to be included in the final result, we will check top 21
    # similar terms, which will include itself.
    query = {
        "query_embedding": term_info["embedding"],
        "from": 0,
        "size": 21
    }
    knn_search_response = search_service.exact_knn_search(query)

    similar_terms = knn_search_response["hits"]["hits"]

    highest_score_per_year = {}

    # Filter for highest score per year
    for obj in similar_terms:
        year = obj['_source']['year_published']
        score = obj['_score']
        # If the year is not in the dictionary or this object has a higher score, update the entry
        if year not in highest_score_per_year or score > highest_score_per_year[year]['_score']:
            highest_score_per_year[year] = obj

    # Convert the dictionary back to a sorted list by year
    sorted_list = sorted(highest_score_per_year.values(), key=lambda x: x['_source']['year_published'])
    return jsonify(sorted_list), HTTPStatus.OK


@search.get("/word_frequencies")
@limiter.limit("30/minute")  # 30 requests per minute
def word_frequencies():
    term_name = request.args.get('term_name')
    if term_name is None:
        return jsonify({"error": "Term name is required!"}), HTTPStatus.BAD_REQUEST

    # Get all term information which have the given term name.
    # assume there are less than 1000 hits
    query = {
        'search_field': "name.keyword",
        'keyword': term_name,
        'exact_match': True,
        'collection': 'Encyclopaedia Britannica',
        'size': 100
    }
    response = search_service.search(query)
    terms = response["hits"]["hits"]
    # Get all descriptions of terms for each year
    year_descriptions = {}
    for term in terms:
        description = term["_source"]["description"]
        year = term["_source"]["year_published"]
        normalised_description = normalize_text(description)
        if year in year_descriptions:
            year_descriptions[year] += " " + normalised_description
        else:
            year_descriptions[year] = normalised_description

    year_word_frequencies = []
    for year in year_descriptions:
        year_description = year_descriptions[year]
        most_common_words = get_word_frequencies(year_description).most_common(40)
        most_common_word_frequencies = [{'text': word, 'value': count} for word, count in most_common_words]
        year_word_frequencies.append({
            "year": year,
            "word_frequencies": most_common_word_frequencies
        })
    sorted_year_word_frequencies = sorted(year_word_frequencies, key=lambda x: x['year'])
    return jsonify(sorted_year_word_frequencies), HTTPStatus.OK


@search.post("/concept_term_records")
@limiter.limit("30/minute")  # 30 requests per minute
def get_term_records_by_concept_uri():
    concept_uri = request.json.get("concept_uri")
    # Get all term information which have the given concept_uri.
    # assume there are less than 100 hits
    query = {
        'search_field': "concept_uri",
        'keyword': concept_uri,
        'exact_match': True,
        'sort': 'year_published',
        'output_fields': ['embedding', 'description', 'year_published', 'vol_title', 'collection', 'sentiment'],
        'size': 100
    }
    response = search_service.search(query)
    terms = response.body["hits"]["hits"]
    results = []
    # add cosine similarity score to terms
    # Iterate through all items except the last one
    for i in range(len(terms)):
        term_dict = {
            "uri":  terms[i]["_id"],
            'description': terms[i]["_source"]['description'],
            'year_published': terms[i]["_source"]['year_published'],
            'source': terms[i]["_source"]['collection'] + ", " + terms[i]["_source"]['vol_title']
        }
        most_common_words = get_word_frequencies(terms[i]["_source"]['description']).most_common(40)
        most_common_word_frequencies = [{'text': word, 'value': count} for word, count in most_common_words]
        term_dict["word_frequencies"] = most_common_word_frequencies
        if "sentiment" in terms[i]["_source"]:
            term_dict["sentiment"] = terms[i]["_source"]["sentiment"]

        if i < len(terms) - 1:
            # Calculate cosine similarity between current item's embedding and the next item's embedding
            similarity = cosine_similarity([terms[i]["_source"]['embedding']], [terms[i + 1]["_source"]['embedding']])[
                0, 0]
            # Add the cosine similarity to the current item
            term_dict["cosine_similarity"] = similarity
        results.append(term_dict)

    # get the latest item record (from wikidata, or dbpedia) linked to this concept
    # get wikidata item linked to this concept
    wiki_items = search_service.get_item_by_concept_uri(concept_uri, "wikidata_items")
    dbpedia_items = search_service.get_item_by_concept_uri(concept_uri, "dbpedia_items")
    latest_item = None
    source = None
    if len(wiki_items) == 1:
        latest_item = wiki_items[0]
        wiki_similarity = cosine_similarity([terms[-1]["_source"]['embedding']],
                                         [wiki_items[0]['embedding']])[0, 0]
        similarity = wiki_similarity
        source = "Wikidata"

    if len(dbpedia_items) == 1:
        latest_item = dbpedia_items[0]
        dbpedia_similarity = cosine_similarity([terms[-1]["_source"]['embedding']],
                                            [dbpedia_items[0]['embedding']])[0, 0]
        similarity = dbpedia_similarity
        source = "DBpedia"

    if len(wiki_items) == 1 and len(dbpedia_items) == 1:
        if wiki_similarity > dbpedia_similarity:
            latest_item = wiki_items[0]
            similarity = wiki_similarity
            source = "Wikidata"

    if latest_item:
        results[-1]["cosine_similarity"] = similarity
        most_common_words = get_word_frequencies(latest_item['item_description']).most_common(40)
        most_common_word_frequencies = [{'text': word, 'value': count} for word, count in most_common_words]
        results.append({
            "uri": latest_item["item_uri"],
            "word_frequencies": most_common_word_frequencies,
            'description': latest_item['item_description'],
            'year_published': datetime.today().year,
            'source': source
        })

    return jsonify(results), HTTPStatus.OK


@search.post("/hto_triples")
@limiter.limit("30/minute")  # 30 requests per minute
def get_hto_triples():
    entry_uri = request.json.get("entry_uri")
    return jsonify(sparql_queries.get_triples(entry_uri)), HTTPStatus.OK