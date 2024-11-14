from .nlp_service import get_sentence_embedding
from ..flask_config import DefaultFlaskConfig

elasticsearch = DefaultFlaskConfig().ELASTIC_SERVICE


def search(query):
    """
    This search function retrieves the most relevant document (term, page) from the elastic search server based on
    keyword, the filtering and sorting options.
    :param query: configurations of the search, the format is:
     query_params = {
        'search type': 'search type',
        'keyword': 'search keyword',
        'sort': 'field name for the sorting',
        'order': 'order name, asc or desc',
        'output_fields': []
        'from': number,
        'size': number,
    }
    :return: elastic search result
    """

    index_names = query.get('index_names', 'hto_*')

    sort_field = query.get('sort', None)
    phrase_match = query.get('phrase_match', False)
    exact_match = query.get('exact_match', False)
    output_fields = ["collection", "vol_title", "name", "note", "alter_names", "genre", "print_location",
                     "year_published", "description"]
    if "output_fields" in query:
        output_fields = query["output_fields"]
    sort = []
    if sort_field:
        sort = [{sort_field: {"order": query.get('order', 'asc')}}]

    # Construct the Elasticsearch query
    body = {
        "query": {
            "bool": {
                "must": [],
                "filter": []
            }
        },
        "_source": output_fields,
        "sort": sort,
        "size": query.get("size", 10),
        "from": query.get("from", 0),
        # Aggregation to get unique filtering options
        "aggs": {
            "unique_collections": {
                "terms": {
                    "field": "collection",
                    "size": 100
                }
            },
            "unique_print_locations": {
                "terms": {
                    "field": "print_location",
                    "size": 100
                }
            }
        }
    }

    keyword = query.get('keyword', '').strip()
    search_field = query.get('search_field', 'full_text')  # Default to full_text if not provided

    search_type = query.get('search_type', 'lexical')
    if search_type == "lexical":
        body["query"] = {
            "bool": {
                    "must": [],
                    "filter": []
                }
        }
        body["highlight"] = {
            "pre_tags": ["<span style='color:orange;'>"],
            "post_tags": ["</span>"],
            "fields": {
                "description": {
                    "fragment_size": 300,
                    "max_analyzed_offset": 100000
                },
                "name": {},
                "alter_names": {},
                "note": {}
            }
        }
        if keyword and keyword != '':
            if exact_match:
                body["query"]["bool"]["must"].append({
                    "term": {
                        search_field: keyword
                    }
                })
            else:
                match_fields = [search_field]
                if search_field == "full_text":
                    match_fields = ["name^2", "alter_names", "note", "description"]
                multi_match_type = "best_fields"
                if phrase_match:
                    multi_match_type = "phrase"
                body["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": keyword,
                        "type": multi_match_type,
                        "fields": match_fields
                    }
                })

        else:
            body["query"]["bool"]["must"].append({"match_all": {}})
    elif search_type == "semantic":
        body["knn"] = {
            "field": "embedding",
            "k": 20,
            "num_candidates": 100,
            "query_vector": get_sentence_embedding(keyword),
            "filter": []
        }

    for field in ['year_published']:
        if field_range := query.get(f'{field}_range', None):
            filter_value = {
                "range": {
                    field: {
                        "gte": field_range.get('gte', None),
                        "lte": field_range.get('lte', None)
                    }
                }
            }
            if search_type == "lexical":
                body["query"]["bool"]["filter"].append(filter_value)
            elif search_type == "semantic":
                body["knn"]["filter"].append(filter_value)

    for field in ["collection", "genre", "print_location", "edition_name"]:
        if value := query.get(field, None):
            filter_value = {
                "term": {
                    field: value
                }
            }
            body["query"]["bool"]["filter"].append(filter_value)
            if search_type == "lexical":
                body["query"]["bool"]["filter"].append(filter_value)
            elif search_type == "semantic":
                body["knn"]["filter"].append(filter_value)

    if "collection" in query:
        if query["collection"] == "Encyclopaedia Britannica":
            body["aggs"]["unique_edition_names"] = {
                "terms": {
                    "field": "edition_name",
                    "size": 100
                }
            }
        else:
            body["aggs"]["unique_vol_titles"] = {
                "terms": {
                    "field": "vol_title",
                    "size": 100
                }
            }
    # Perform the search
    #print(body)
    response = elasticsearch.search(index=index_names, body=body)
    return response


def get_term_info(term_uri):
    index_name = 'hto_eb'
    response = elasticsearch.get(index=index_name, id=term_uri)
    result = response['_source']
    return result


def get_item_by_concept_uri(concept_uri, index_name):
    query = {
        "query": {
            "term": {
                "concept_uri": concept_uri
            }
        }
    }

    # Execute the search query
    response = elasticsearch.search(index=index_name, body=query)

    # Extract documents from the response
    documents = [hit["_source"] for hit in response['hits']['hits']]
    return documents


def exact_knn_search(query):
    """
    This search function retrieves the most relevant document (term, page) from the elastic search server based on
    the embeddings of the term descriptions. Exact, brute-force kNN guarantees accurate results but doesn’t scale well
    with large datasets. With this approach, a script_score query must scan each matching document to compute the vector
    function, which can result in slow search speeds.
    :param query: configurations of the search, the format is:
     query_params = {
        'query_embedding': [],
        'from': number,
        'size': number,
    }
    :return: elastic search result
    """
    index_name = "hto_eb"
    body = {
        "size": query.get('size', 20),
        "from": query.get('from', 0),
        "query": {
            "script_score": {
                "query": {
                    "match_all": {}
                },
                "script": {
                    "source": "cosineSimilarity(params.query_embedding, 'embedding') + 1.0",
                    "params": {
                        "query_embedding": query.get('query_embedding')
                    }
                }
            }
        }
    }
    response = elasticsearch.search(index=index_name, body=body)
    return response
