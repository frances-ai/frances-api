from SPARQLWrapper import SPARQLWrapper, JSON
from .utils import get_kg_url
from ..resolver import get_hto_kg_endpoint
from rdflib import Namespace

hto = Namespace("https://w3id.org/hto#")
hto_endpoint = get_hto_kg_endpoint()

sparqlW = SPARQLWrapper(hto_endpoint)


def get_editor():
    sparqlW.setQuery("""
        PREFIX eb: <https://w3id.org/eb#>
        SELECT DISTINCT ?name
        WHERE {
        ?instance eb:editor ?Editor.
        ?Editor eb:name ?name .
       }
    """)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    return results["results"]["bindings"][0]["name"]["value"]


def get_editions():
    # Title: Edition 1,1771
    query = """
    PREFIX hto: <https://w3id.org/hto#>
    SELECT ?title ?e ?y ?number WHERE {
           ?e a hto:Edition ;
                hto:title ?title;
                hto:yearPublished ?y.
            OPTIONAL {?e hto:number ?number}
        } ORDER BY ASC(?y)"""
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = []
    for r in results["results"]["bindings"]:
        edition_name = r["title"]["value"]
        # Edition 0,1801 is the supplement to the third edition of the Encyclopaedia Britannica.
        if "number" in r:
            edition_number = r["number"]["value"]
            year_published = r["y"]["value"]
            edition_name = f"Edition {edition_number}, {year_published}"

        clean_r.append({
            "uri": r["e"]["value"],
            "name": edition_name
        })

    return clean_r


def get_clean_series_title(title):
    title_removed_collection_name = title
    split_str = title.split("_")
    if len(split_str) == 2:
        title_removed_collection_name = split_str[1]

    return title_removed_collection_name


def get_series(collection_name):
    query = """
    PREFIX hto: <https://w3id.org/hto#>
    SELECT ?title ?s ?y WHERE {
            ?collection a hto:WorkCollection;
                hto:name '%s'.
                
           ?s a hto:Series;
                hto:title ?title ;
                hto:yearPublished ?y.

        } ORDER BY ASC(?y)""" % (collection_name + " Collection")
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = []
    for r in results["results"]["bindings"]:
        clean_r.append({
            "uri": r["s"]["value"],
            "name": get_clean_series_title(r["title"]["value"])
        })
    return clean_r


def get_volumes(uri):
    query = """
            PREFIX hto: <https://w3id.org/hto#>
            SELECT * WHERE {
               %s hto:hadMember ?v .
               ?v a hto:Volume;
                  hto:number ?vnum ; 
                  hto:title ?title.
            } 
            """ % (uri)
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = []
    for r in results["results"]["bindings"]:
        uri = r["v"]["value"]
        number = r["vnum"]["value"]
        title = r["title"]["value"]
        if 'edition' in title and 'Volume' in title:
            name = title[title.find("Volume"):]
        else:
            name = title
        clean_r.append({
            "uri": uri,
            "number": number,
            "name": name
        })
    return clean_r


def get_numberOfVolumes(uri):
    query = """
    PREFIX hto: <https://w3id.org/hto#>
    SELECT (COUNT (DISTINCT ?v) as ?count)
        WHERE {
            %s hto:hadMember ?v.
    	    ?v a hto:Volume. 
    }
    """ % (uri)
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    return results["results"]["bindings"][0]["count"]["value"]


def get_edition_details(uri):
    query = """
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?genre ?yearPublished ?num ?title ?subtitle ?printedAt ?physicalDescription ?mmsid ?shelfLocator ?numberOfVolumes  WHERE {
           %s hto:yearPublished ?yearPublished;
              hto:title ?title;
              hto:printedAt ?printed_uri;
              hto:physicalDescription ?physicalDescription;
              hto:mmsid ?mmsid;
              hto:shelfLocator ?shelfLocator_uri;
              hto:genre ?genre. 
            ?printed_uri rdfs:label ?printedAt.
            ?shelfLocator_uri rdfs:label ?shelfLocator.
            OPTIONAL {%s hto:subtitle ?subtitle}
            OPTIONAL {%s hto:number ?num}
    }
    """ % (uri, uri, uri)
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = {}
    for r in results["results"]["bindings"]:
        edition_title = r["title"]["value"]
        # Edition 0,1801 is the supplement to the third edition of the Encyclopaedia Britannica.
        if "Edition 0,1801" == edition_title:
            edition_title = "Sup. Edition 3, 1801"

        clean_r["title"] = edition_title
        clean_r["year"] = r["yearPublished"]["value"]
        number = 0
        if "num" in r:
            number = r["num"]["value"]
        clean_r["uri"] = uri

        if "subtitle" in r:
            clean_r["subtitle"] = r["subtitle"]["value"]
        clean_r["number"] = number
        clean_r["printedAt"] = r["printedAt"]["value"]
        clean_r["physicalDescription"] = r["physicalDescription"]["value"]
        clean_r["MMSID"] = r["mmsid"]["value"]
        clean_r["shelfLocator"] = r["shelfLocator"]["value"]
        clean_r["genre"] = r["genre"]["value"]
        clean_r["language"] = "English"
        clean_r["numOfVolumes"] = get_numberOfVolumes(uri)

    return clean_r


def get_series_details(uri):
    query = """
    PREFIX hto: <https://w3id.org/hto#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?genre ?yearPublished ?num ?title ?subtitle ?printedAt ?physicalDescription ?mmsid ?shelfLocator ?numberOfVolumes  WHERE {
           %s hto:yearPublished ?yearPublished;
              hto:title ?title;
              hto:printedAt ?printed_uri;
              hto:physicalDescription ?physicalDescription;
              hto:mmsid ?mmsid;
              hto:shelfLocator ?shelfLocator_uri;
              hto:genre ?genre. 
            ?printed_uri rdfs:label ?printedAt.
            ?shelfLocator_uri rdfs:label ?shelfLocator.
            OPTIONAL {%s hto:subtitle ?subtitle}
            OPTIONAL {%s hto:number ?num}
    }
    """ % (uri, uri, uri)
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = {}
    for r in results["results"]["bindings"]:
        clean_r["title"] = r["title"]["value"]
        clean_r["year"] = r["yearPublished"]["value"]
        number = 0
        if "num" in r:
            number = r["num"]["value"]
        clean_r["uri"] = uri

        if "subtitle" in r:
            clean_r["subtitle"] = r["subtitle"]["value"]
        clean_r["number"] = number
        clean_r["printedAt"] = r["printedAt"]["value"]
        clean_r["physicalDescription"] = r["physicalDescription"]["value"]
        clean_r["MMSID"] = r["mmsid"]["value"]
        clean_r["shelfLocator"] = r["shelfLocator"]["value"]
        clean_r["genre"] = r["genre"]["value"]
        clean_r["language"] = "English"
        clean_r["numOfVolumes"] = get_numberOfVolumes(uri)

    return clean_r


def get_volume_details(uri):
    uri_s = "<" + uri + ">"
    query = """
            PREFIX hto: <https://w3id.org/hto#>
            SELECT ?num ?title ?part ?volumeId ?permanentURL ?numberOfPages ?letters WHERE {
               %s hto:number ?num;
                  hto:title ?title;
                  hto:volumeId ?volumeId;
                  hto:permanentURL ?permanentURL;
                  hto:numberOfPages ?numberOfPages;
               OPTIONAL {%s hto:letters ?letters. }         
               OPTIONAL {%s hto:part ?part. }      
            }
            """ % (uri_s, uri_s, uri_s)

    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = {}
    if len(results["results"]["bindings"]) == 1:
        r = results["results"]["bindings"][0]
        clean_r["number"] = r["num"]["value"]
        clean_r["uri"] = uri
        clean_r["title"] = r["title"]["value"]
        clean_r["id"] = r["volumeId"]["value"]
        if "letters" in r:
            clean_r["letters"] = r["letters"]["value"]
        if "part" in r:
            clean_r["part"] = r["part"]["value"]
        clean_r["permanentURL"] = r["permanentURL"]["value"]
        clean_r["numOfPages"] = r["numberOfPages"]["value"]
    return clean_r

def get_es_full_details(uri):
    uri_s = "<" + uri + ">"
    query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hto: <https://w3id.org/hto#>
            SELECT * WHERE {
                %s hto:yearPublished ?yearPublished;
                   hto:title ?es_title;
                   hto:printedAt ?printed_uri;
                   hto:physicalDescription ?physicalDescription;
                   hto:mmsid ?mmsid;
                   hto:shelfLocator ?shelfLocator_uri;
                   hto:genre ?genre. 
                   ?printed_uri rdfs:label ?printedAt.
                   ?shelfLocator_uri rdfs:label ?shelfLocator.
               OPTIONAL {%s hto:subtitle ?es_subtitle}
               OPTIONAL {%s hto:number ?es_num}
                ?collection hto:hadMember %s;
                    hto:name ?collection_name.    
            }
            """ % (uri_s, uri_s, uri_s, uri_s)

    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = {}
    if len(results["results"]["bindings"]) == 1:
        r = results["results"]["bindings"][0]
        clean_r["collection"] = {
            "name": r["collection_name"]["value"],
            "uri": r["collection"]["value"]
        }
        es_number = 0
        if "es_num" in r:
            es_number = r["es_num"]["value"]
        edition_series = {
            "title": r["es_title"]["value"],
            "year": r["yearPublished"]["value"],
            "number": es_number,
            "uri": uri,
            "printedAt": r["printedAt"]["value"],
            "physicalDescription": r["physicalDescription"]["value"],
            "MMSID": r["mmsid"]["value"],
            "shelfLocator": r["shelfLocator"]["value"],
            "genre": r["genre"]["value"],
            "language": "English"
        }
        if "es_subtitle" in r:
            edition_series["subtitle"] = r["es_subtitle"]["value"]
        if "Encyclopaedia Britannica" in clean_r["collection"]["name"]:
            clean_r["edition"] = edition_series
            es_type = "edition"
        else:
            clean_r["series"] = edition_series
            es_type = "series"
    return clean_r, es_type


def get_volume_full_details(uri):
    uri_s = "<" + uri + ">"
    query = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX hto: <https://w3id.org/hto#>
            SELECT * WHERE {
                %s a hto:Volume;
                    hto:number ?vol_num;
                    hto:title ?vol_title;
                    hto:volumeId ?volumeId;
                    hto:permanentURL ?vol_permanentURL;
                    hto:numberOfPages ?vol_numberOfPages;
                OPTIONAL {%s hto:letters ?letters. }         
                OPTIONAL {%s hto:part ?part. }  
                ?es hto:hadMember %s;
                    hto:yearPublished ?yearPublished;
                   hto:title ?es_title;
                   hto:printedAt ?printed_uri;
                   hto:physicalDescription ?physicalDescription;
                   hto:mmsid ?mmsid;
                   hto:shelfLocator ?shelfLocator_uri;
                   hto:genre ?genre. 
                   ?printed_uri rdfs:label ?printedAt.
                   ?shelfLocator_uri rdfs:label ?shelfLocator.
               OPTIONAL {?es hto:subtitle ?es_subtitle}
               OPTIONAL {?es hto:number ?es_num}
                ?collection hto:hadMember ?es;
                    hto:name ?collection_name.    
            }
            """ % (uri_s, uri_s, uri_s, uri_s)

    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = {}
    if len(results["results"]["bindings"]) == 1:
        r = results["results"]["bindings"][0]
        clean_r['volume'] = {
            "number": r["vol_num"]["value"],
            "uri": uri,
            "title": r["vol_title"]["value"],
            "id": r["volumeId"]["value"],
            "permanentURL": r["vol_permanentURL"]["value"],
            "numberOfPages": r["vol_numberOfPages"]["value"]
        }
        clean_r["collection"] = {
            "name": r["collection_name"]["value"],
            "uri": r["collection"]["value"]
        }
        es_number = 0
        if "es_num" in r:
            es_number = r["es_num"]["value"]
        edition_series = {
            "title": r["es_title"]["value"],
            "year": r["yearPublished"]["value"],
            "number": es_number,
            "uri": r["es"]["value"],
            "printedAt": r["printedAt"]["value"],
            "physicalDescription": r["physicalDescription"]["value"],
            "MMSID": r["mmsid"]["value"],
            "shelfLocator": r["shelfLocator"]["value"],
            "genre": r["genre"]["value"],
            "language": "English"
        }
        if "es_subtitle" in r:
            edition_series["subtitle"] = r["es_subtitle"]["value"]
        if "Encyclopaedia Britannica" in clean_r["collection"]["name"]:
            clean_r["edition"] = edition_series
        else:
            clean_r["series"] = edition_series
    return clean_r


def get_definition(term=None, documents=None, uris=None):
    term = term.upper()
    query1 = """
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?definition ?b  ?spnum ?epnum ?year ?vnum ?enum ?rn ?permanentURL WHERE {{
    	?b a eb:Article .
    	?b eb:name ?a .
        ?b eb:name "%s" .
        ?b eb:definition ?definition . 
        OPTIONAL {?b eb:relatedTerms ?rt. 
                  ?rt eb:name ?rn. }
       ?e eb:hasPart ?v.
       ?v eb:number ?vnum.
       ?v eb:permanentURL ?permanentURL.
       ?v eb:hasPart ?b.
       ?e eb:publicationYear ?year.
       ?e eb:number ?enum.
       ?b eb:startsAtPage ?sp.
       ?sp eb:number ?spnum .
       ?b eb:endsAtPage ?ep.
       ?ep eb:number ?epnum . }

       UNION {
    	?b a eb:Topic .
    	?b eb:name ?a .
        ?b eb:name "%s" .
        ?b eb:definition ?definition 
        
        OPTIONAL {?b eb:relatedTerms ?rt. 
                  ?rt eb:name ?rn. }
        
        ?e eb:hasPart ?v.
        ?v eb:number ?vnum.
        ?v eb:permanentURL ?permanentURL.
        ?v eb:hasPart ?b.
        ?e eb:publicationYear ?year.
        ?e eb:number ?enum.
        ?b eb:startsAtPage ?sp.
        ?sp   eb:number ?spnum .
        ?b eb:endsAtPage ?ep.
        ?ep eb:number ?epnum .
        
        }
   } ORDER BY ASC(?year)
   """ % (term, term)
    query = query1
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r = {}
    list_terms = {}
    cont = 0
    for r in results["results"]["bindings"]:
        permanentURL = r["permanentURL"]["value"]
        startPermanentURL = permanentURL + "#?c=0&m=0&s=0&cv=" + r["spnum"]["value"]
        endPermanentURL = permanentURL + "#?c=0&m=0&s=0&cv=" + r["epnum"]["value"]

        if "Article" in r["b"]["value"]:
            term_type = "Article"
            definition = r["definition"]["value"]
        else:
            try:
                term_type = "Topic"
                indice = uris.index(r["b"]["value"])
                definition = "Summary: " + documents[indice]
            except:
                term_type = "Topic"
                definition = r["definition"]["value"][0:100]

        if "rn" in r:
            if r["b"]["value"] not in list_terms:
                list_terms[r["b"]["value"]] = []
            if r["rn"]["value"] not in list_terms[r["b"]["value"]]:
                list_terms[r["b"]["value"]].append(r["rn"]["value"])
            clean_r[r["b"]["value"]] = [r["year"]["value"], r["enum"]["value"], r["vnum"]["value"],
                                        [startPermanentURL, r["spnum"]["value"]],
                                        [endPermanentURL, r["epnum"]["value"]], term_type, definition,
                                        list_terms[r["b"]["value"]]]
        else:
            clean_r[r["b"]["value"]] = [r["year"]["value"], r["enum"]["value"], r["vnum"]["value"],
                                        [startPermanentURL, r["spnum"]["value"]],
                                        [endPermanentURL, r["epnum"]["value"]], term_type, definition, []]
    return clean_r


def get_eb_vol_statistics(uri):
    uri_s = "<" + uri + ">"
    data = {}
    ###### NUM ARTICLES
    query = """
          PREFIX hto: <https://w3id.org/hto#>
          SELECT (COUNT (DISTINCT ?t) as ?count)
          WHERE {
          %s hto:hadMember ?p .
          ?p a hto:Page;
            hto:hadMember ?t.
          ?t a hto:ArticleTermRecord.
         } 
         """ % (uri_s)
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    num_articles = results["results"]["bindings"][0]["count"]["value"]
    data["numOfArticles"] = num_articles

    ###### NUM TOPICS
    query1 = """
              PREFIX hto: <https://w3id.org/hto#>
              SELECT (COUNT (DISTINCT ?t) as ?count)
              WHERE {
              %s hto:hadMember ?p .
              ?p a hto:Page;
                hto:hadMember ?t.
              ?t a hto:TopicTermRecord.
             } 
             """ % (uri_s)
    sparqlW.setQuery(query1)
    sparqlW.setReturnFormat(JSON)
    results1 = sparqlW.query().convert()
    num_topics = results1["results"]["bindings"][0]["count"]["value"]
    data["numOfTopics"] = num_topics

    ###### NUM DIST ARTICLES
    query2 = """
         PREFIX hto: <https://w3id.org/hto#>
         PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
         SELECT (count (DISTINCT ?a) as ?count)
         WHERE {
            %s hto:hadMember ?p .
              ?p a hto:Page;
                hto:hadMember ?t.
              ?t a hto:ArticleTermRecord;
                hto:name ?a.
        }
        """ % (uri_s)
    sparqlW.setQuery(query2)
    sparqlW.setReturnFormat(JSON)
    results2 = sparqlW.query().convert()
    num_dist_articles = results2["results"]["bindings"][0]["count"]["value"]
    data["NumOfDistinctArticles"] = num_dist_articles

    ###### NUM DIST TOPICS
    query3 = """
       PREFIX hto: <https://w3id.org/hto#>
       PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
       SELECT (count (DISTINCT ?a) as ?count)
       WHERE {
            %s hto:hadMember ?p .
              ?p a hto:Page;
                hto:hadMember ?t.
              ?t a hto:TopicTermRecord;
                hto:name ?a.
      }
      """ % (uri_s)
    sparqlW.setQuery(query3)
    sparqlW.setReturnFormat(JSON)
    results3 = sparqlW.query().convert()
    num_dist_topics = results3["results"]["bindings"][0]["count"]["value"]
    data["NumOfDistinctTopics"] = num_dist_topics
    return data


def get_nls_document_page_image_url(page_permanent_url):
    if page_permanent_url is None:
        return None
    # get the page id
    page_id = page_permanent_url.split("/")[-1]
    # construct the image url
    tmp_id = str(int(page_id) + 2)

    if 97343436 <= int(page_id) <= 97504499:
        # gazetteers of scotland
        # https://deriv.nls.uk/dcn30/<first 4 digits of the tmp_id>/<tmp_id>.30.jpg
        page_image_url = f"https://deriv.nls.uk/dcn30/{tmp_id[:4]}/{tmp_id}.30.jpg"
    else:
        # https://deriv.nls.uk/dcn30/<first 4 digits of the tmp_id>/<second 4 digits of the tmp_id>/<tmp_id>.30.jpg
        page_image_url = f"https://deriv.nls.uk/dcn30/{tmp_id[:4]}/{tmp_id[4:8]}/{tmp_id}.30.jpg"
    return page_image_url


def get_page_display_info(page_uri):
    result = {}
    hto_sparql = SPARQLWrapper(hto_endpoint)
    hto_sparql.setReturnFormat(JSON)
    query = """
            PREFIX hto: <https://w3id.org/hto#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT * WHERE {
                %s a hto:Page;
                    hto:number ?number;
                    hto:permanentURL ?permanentURL.}
            """ % page_uri
    # print(query)
    hto_sparql.setQuery(query)
    try:
        ret = hto_sparql.queryAndConvert()
        r = ret["results"]["bindings"][0]
        permanent_url = r["permanentURL"]["value"]
        image_url = get_nls_document_page_image_url(permanent_url)
        result = {
            "number": r["number"]["value"],
            "permanent_url": r["permanentURL"]["value"],
            "image_url": image_url
        }
    except Exception as e:
        print(e)

    # print(result)
    return result


def get_page_info(page_uri):
    result = {}
    hto_sparql = SPARQLWrapper(hto_endpoint)
    hto_sparql.setReturnFormat(JSON)
    query = """
            PREFIX hto: <https://w3id.org/hto#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT * WHERE {
                %s a hto:Page;
                    hto:number ?number.
                OPTIONAL {%s hto:permanentURL ?page_permanent_url}
                ?vol a hto:Volume;
                    hto:title ?vol_title;
                    hto:hadMember %s;
                    hto:permanentURL ?volume_permanent_url.
                ?edition_or_series a ?document_type;
                    hto:hadMember ?vol;
                    hto:yearPublished ?year_published;
                    hto:genre ?genre;
                    hto:printedAt ?printedAt.
                FILTER (?document_type = hto:Edition || ?document_type = hto:Series)
                ?printedAt rdfs:label ?print_location.
                ?collection hto:hadMember ?edition_or_series;
                    hto:name ?collection_name.   
            }
            """ % (page_uri, page_uri, page_uri)
    # print(query)
    hto_sparql.setQuery(query)
    try:
        ret = hto_sparql.queryAndConvert()
        r = ret["results"]["bindings"][0]
        page_permanent_url = None
        if "page_permanent_url" in r:
            page_permanent_url = r["page_permanent_url"]["value"]
        year_published = r["year_published"]["value"]
        image_url = get_nls_document_page_image_url(page_permanent_url)
        result = {
            "collection": {
                "name": r["collection_name"]["value"],
                "uri": r["collection"]["value"]
            },
            "volume": {
                "title": r["vol_title"]["value"],
                "uri": r["vol"]["value"],
                "permanent_url": r["volume_permanent_url"]["value"]
            },
            "edition_or_series": {
                "type": r["document_type"]["value"],
                "uri": r["edition_or_series"]["value"],
                "genre": r["genre"]["value"],
                "print_location": r["print_location"]["value"],
                "year_published": year_published
            },
            "number": r["number"]["value"],
            "permanent_url": page_permanent_url,
            "image_url": image_url
        }
    except Exception as e:
        print(e)
    contents = get_page_content(page_uri)
    result["contents"] = contents
    # print(result)
    return result


def get_page_content(page_uri):
    result = []
    hto_sparql = SPARQLWrapper(hto_endpoint)
    hto_sparql.setReturnFormat(JSON)
    query = """
            PREFIX hto: <https://w3id.org/hto#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT * WHERE {
                %s a ?page;
                    hto:hasOriginalDescription ?desc.
                ?desc hto:text ?description_content;
                    hto:hasTextQuality ?textQuality.
                }
            """ % page_uri
    # print(query)
    hto_sparql.setQuery(query)
    try:
        ret = hto_sparql.queryAndConvert()
        for r in ret["results"]["bindings"]:
            result.append({
                "uri": r["desc"]["value"],
                "description": r["description_content"]["value"],
                "text_quality": r["textQuality"]["value"]
            })
    except Exception as e:
        print(e)

    # print(result)
    return result


def get_term_definitions(term_uri):
    result = []
    hto_sparql = SPARQLWrapper(hto_endpoint)
    hto_sparql.setReturnFormat(JSON)
    query = """
            PREFIX hto: <https://w3id.org/hto#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT * WHERE {
                %s a ?term_type;
                    hto:hasOriginalDescription ?desc.
                FILTER (?term_type = hto:ArticleTermRecord || ?term_type = hto:TopicTermRecord)
                ?desc hto:text ?description_content;
                    hto:hasTextQuality ?textQuality.
                }
            """ % term_uri
    # print(query)
    hto_sparql.setQuery(query)
    try:
        ret = hto_sparql.queryAndConvert()
        for r in ret["results"]["bindings"]:
            result.append({
                "uri": r["desc"]["value"],
                "description": r["description_content"]["value"],
                "text_quality": r["textQuality"]["value"]
            })
    except Exception as e:
        print(e)

    # print(result)
    return result


def get_term_info(term_uri):
    """
    This function retrieves the metadata, and textual content of a term record in knowledge graph.
    :param term_path: the path of a term
    :return: the metadata, and textual content of a term, the format is:
    {
        name: "Term name",
        alter_names: [],
        note: "",
        type: "Article",
        collection: {
            name: "Encyclopaedia Britannica",
            uri: ''
        }
        volume: {
            title: "",
            uri: ''
        }
        year_published: "",
        genre: "encyclopedia",
        print_location: "Edinburgh"
        start_page: {
            number: 1,
            uri: ''
        },
        end_page: {
            number: 1,
            uri: ''
        }
        descriptions: [
        {
            description: '',
            uri: '',
            text_quality: ''
        }
        ]
    }
    """
    term_uri = "<" + term_uri + ">"
    result = {}
    hto_sparql = SPARQLWrapper(hto_endpoint)
    hto_sparql.setReturnFormat(JSON)
    query = """
        PREFIX hto: <https://w3id.org/hto#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT * WHERE {
            %s a ?term_type;
                hto:name ?name;
                hto:startsAtPage ?start_page;
                hto:endsAtPage ?end_page;
            OPTIONAL {%s hto:note ?note}
            FILTER (?term_type = hto:ArticleTermRecord || ?term_type = hto:TopicTermRecord)
            ?start_page hto:number ?s_page_num.
  			OPTIONAL {?start_page hto:permanentURL ?start_page_permanent_url}
            ?end_page hto:number ?e_page_num.
  			OPTIONAL {?end_page hto:permanentURL ?end_page_permanent_url}
            ?vol a hto:Volume;
                hto:title ?vol_title;
                hto:hadMember ?start_page;
                hto:permanentURL ?volume_permanent_url.
            ?edition a hto:Edition;
                hto:hadMember ?vol;
                hto:yearPublished ?year_published;
                hto:genre ?genre;
                hto:printedAt ?printedAt.
            ?printedAt rdfs:label ?print_location.
            ?collection hto:hadMember ?edition;
                hto:name ?collection_name.
            }
        """ % (term_uri, term_uri)
    # print(query)
    hto_sparql.setQuery(query)
    try:
        ret = hto_sparql.queryAndConvert()
        r = ret["results"]["bindings"][0]
        note = None
        if "note" in r:
            note = r["note"]["value"]
        term_type = "Article" if r["term_type"]["value"] == str(hto.ArticleTermRecord) else "Topic"
        start_page_num = r["s_page_num"]["value"]
        start_page_permanent_url = None
        if "start_page_permanent_url" in r:
            start_page_permanent_url = r["start_page_permanent_url"]["value"]
        end_page_permanent_url = None
        if "end_page_permanent_url" in r:
            end_page_permanent_url = r["end_page_permanent_url"]["value"]
        end_page_num = r["e_page_num"]["value"]
        year_published = r["year_published"]["value"]
        term_name = r["name"]["value"]
        result = {
            "collection": {
                "name": r["collection_name"]["value"],
                "uri": r["collection"]["value"]
            },
            "volume": {
                "title": r["vol_title"]["value"],
                "uri": r["vol"]["value"],
                "permanent_url": r["volume_permanent_url"]["value"]
            },
            "edition": {
                "uri": r["edition"]["value"],
                "genre": r["genre"]["value"],
                "print_location": r["print_location"]["value"],
                "year_published": year_published
            },
            "note": note,
            "term_name": term_name,
            "term_type": term_type,
            "start_page": {
                "number": start_page_num,
                "uri": r["start_page"]["value"],
                "permanent_url": start_page_permanent_url
            },
            "end_page": {
                "number": end_page_num,
                "uri": r["end_page"]["value"],
                "permanent_url": end_page_permanent_url
            }
        }
    except Exception as e:
        print(e)

    descriptions = get_term_definitions(term_uri)
    result["descriptions"] = descriptions
    # print(result)
    return result


def get_triples(entry_uri):
    if entry_uri is None:
        return None
    entry_uri = "<" + entry_uri + ">"
    hto_sparql = SPARQLWrapper(hto_endpoint)
    hto_sparql.setReturnFormat(JSON)
    hto_sparql.setQuery("""
        SELECT * WHERE {
            %s ?pre ?obj
        }
        """ % entry_uri)
    try:
        ret = hto_sparql.queryAndConvert()
        return ret["results"]["bindings"]
    except Exception as e:
        print(e)
        return None


if __name__ == "__main__":
    # get volume details with edition info
    print(get_series("Chapbooks printed in Scotland"))
