from SPARQLWrapper import SPARQLWrapper, JSON

from ..resolver import get_kg_url

eb_url = get_kg_url('total_eb')

sparqlW = SPARQLWrapper(eb_url)


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


def describe_resource(uri=None, kg_type="total_eb"):
    kg_url = get_kg_url(kg_type)
    sparql = SPARQLWrapper(kg_url)
    if kg_type == "total_eb":
        prefix = "eb"
    else:
        prefix = "nls"

    query = """
    PREFIX %s: <https://w3id.org/%s#>
    DESCRIBE %s 
    """ % (prefix, prefix, uri)
    sparql.setQuery(query)
    results = sparql.query().convert()
    clear_r = []
    for s, p, o in results.triples((None, None, None)):
        data = {}
        sub = str(s)
        if "#" in sub:
            sub = sub.split("#")[1]
            sub = prefix + ":" + sub
        data["subject"] = sub
        pred = str(p)
        if "#" in pred:
            pred = pred.split("#")[1]
            pred = prefix + ":" + pred
        data["predicate"] = pred
        obj = str(o)
        if "#" in obj:
            obj = obj.split("#")[1]
            obj = prefix + ":" + obj

        if len(obj) > 80:
            obj = obj[0:80]
            obj = obj + "... CONTINUE"

        data["object"] = obj
        clear_r.append(data)

    startsAtPage = "-1"
    endsAtPage = "-2"

    for i in range(0, len(clear_r)):
        if "startsAtPage" in clear_r[i]["predicate"]:
            startsAtPage = clear_r[i]["object"]
        if "endsAtPage" in clear_r[i]["predicate"]:
            endsAtPage = clear_r[i]["object"]
            endsAtPageIndex = i

    if startsAtPage == endsAtPage:
        clear_r.pop(endsAtPageIndex)
    return clear_r


def get_vol_by_vol_uri(uri):
    sparql = SPARQLWrapper(eb_url)
    query = """
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?vnum ?letters ?part WHERE {
       %s eb:number ?vnum ;
          eb:letters ?letters .
           OPTIONAL {%s eb:part ?part; }
       
    
    } """ % (uri, uri)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    r = results["results"]["bindings"][0]
    if "part" in r:
        data = r["vnum"]["value"] + " " + r["letters"]["value"] + "Part " + r["part"]["value"]
    else:
        data = r["vnum"]["value"] + " " + r["letters"]["value"]
    return data


def get_editions():
    sparql = SPARQLWrapper(eb_url)
    # Title: Edition 1,1771
    query = """
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?title ?e ?y WHERE {
           ?e a eb:Edition ;
                eb:title ?title;
                eb:publicationYear ?y.
        } ORDER BY ASC(?y)"""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r = []
    for r in results["results"]["bindings"]:
        clean_r.append({
            "uri": r["e"]["value"],
            "name": r["title"]["value"]
        })
    clean_r.append({
        "uri": 'https://w3id.org/eb/i/Edition/9910796343804340',
        "name": 'Sup. Edition 3, 1801'
    })
    return clean_r


def get_clean_serie_title(title):
    title_removed_collection_name = title
    split_str = title.split("_")
    if len(split_str) == 2:
        title_removed_collection_name = split_str[1]

    return title_removed_collection_name


def get_series(kg_type):
    kg_url = get_kg_url(kg_type)
    sparql = SPARQLWrapper(kg_url)
    query = """
    PREFIX nls: <https://w3id.org/nls#>
    SELECT ?title ?s ?y WHERE {
           ?s a nls:Serie ;
                nls:title ?title ;
                nls:publicationYear ?y.

        } ORDER BY ASC(?y)"""
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r = []
    for r in results["results"]["bindings"]:

        clean_r.append({
            "uri": r["s"]["value"],
            "name": get_clean_serie_title(r["title"]["value"])
        })
    return clean_r


def get_volumes(kg_type, uri):
    kg_url = get_kg_url(kg_type)
    sparql = SPARQLWrapper(kg_url)
    if kg_type == "total_eb":
        prefix = "eb"
        display_attr = "letters"
    else:
        prefix = "nls"
        display_attr = "title"

    query = """
    PREFIX %s: <https://w3id.org/%s#>
    SELECT ?v ?vnum ?part ?%s WHERE {
       %s %s:hasPart ?v .
       ?v %s:number ?vnum ; 
          %s:%s ?%s .
          OPTIONAL {?v %s:part ?part; }
    } 
    """ % (prefix, prefix, display_attr, uri, prefix, prefix, prefix, display_attr, display_attr, prefix)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r = []
    for r in results["results"]["bindings"]:
        uri = r["v"]["value"]
        number = r["vnum"]["value"]
        if "part" in r:
            name = number + " " + r[display_attr]["value"] + "Part " + r["part"]["value"]
        else:
            name = number + " " + r[display_attr]["value"]
        clean_r.append({
            "uri": uri,
            "number": number,
            "name": name
        })
    return clean_r


def get_numberOfVolumes(sparql, prefix, uri):
    query = """
    PREFIX %s: <https://w3id.org/%s#>
    SELECT (COUNT (DISTINCT ?v) as ?count)
        WHERE {
            %s %s:hasPart ?v.
    	    ?v ?b ?c
    }
    """ % (prefix, prefix, uri, prefix)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"][0]["count"]["value"]


def get_edition_details(uri=None):
    sparql = SPARQLWrapper(eb_url)
    if not uri:
        uri = "<https://w3id.org/eb/i/Edition/992277653804341>"
    query = """
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?genre ?publicationYear ?num ?title ?subtitle ?printedAt ?physicalDescription ?mmsid ?shelfLocator ?numberOfVolumes  WHERE {
           %s eb:publicationYear ?publicationYear ;
              eb:number ?num;
              eb:title ?title;
              eb:subtitle ?subtitle ;
              eb:printedAt ?printedAt;
              eb:physicalDescription ?physicalDescription;
              eb:mmsid ?mmsid;
              eb:shelfLocator ?shelfLocator;
              eb:genre ?genre. 
    }
    """ % (uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r = {}
    for r in results["results"]["bindings"]:
        clean_r["year"] = r["publicationYear"]["value"]
        clean_r["number"] = r["num"]["value"]
        clean_r["uri"] = uri
        clean_r["title"] = r["title"]["value"]
        if "subtitle" in r:
            clean_r["subtitle"] = r["subtitle"]["value"]
        clean_r["printedAt"] = r["printedAt"]["value"]
        clean_r["physicalDescription"] = r["physicalDescription"]["value"]
        clean_r["MMSID"] = r["mmsid"]["value"]
        clean_r["shelfLocator"] = r["shelfLocator"]["value"]
        clean_r["genre"] = r["genre"]["value"]
        clean_r["language"] = "English"
        clean_r["numOfVolumes"] = get_numberOfVolumes(sparql, "eb", uri)

    return clean_r


def get_serie_details(kg_type, uri=None):
    kg_url = get_kg_url(kg_type)
    sparql = SPARQLWrapper(kg_url)
    if not uri:
        uri = "<https://w3id.org/eb/i/Edition/992277653804341>"
    query = """
    PREFIX nls: <https://w3id.org/nls#>
    SELECT ?genre ?publicationYear ?num ?title ?subtitle ?printedAt ?physicalDescription ?mmsid ?shelfLocator ?numberOfVolumes  WHERE {
           %s nls:publicationYear ?publicationYear ;
              nls:number ?num;
              nls:title ?title;
              nls:subtitle ?subtitle ;
              nls:printedAt ?printedAt;
              nls:physicalDescription ?physicalDescription;
              nls:mmsid ?mmsid;
              nls:shelfLocator ?shelfLocator;
              nls:genre ?genre. 
    }
    """ % (uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r = {}
    for r in results["results"]["bindings"]:
        clean_r["year"] = r["publicationYear"]["value"]
        clean_r["number"] = r["num"]["value"]
        clean_r["uri"] = uri
        clean_r["title"] = r["title"]["value"]
        if "subtitle" in r:
            clean_r["subtitle"] = r["subtitle"]["value"]
        clean_r["printedAt"] = r["printedAt"]["value"]
        clean_r["physicalDescription"] = r["physicalDescription"]["value"]
        clean_r["MMSID"] = r["mmsid"]["value"]
        clean_r["shelfLocator"] = r["shelfLocator"]["value"]
        clean_r["genre"] = r["genre"]["value"]
        clean_r["language"] = "English"
        clean_r["numOfVolumes"] = get_numberOfVolumes(sparql, "nls", uri)

    return clean_r


def get_volume_details(kg_type, uri=None):
    kg_url = get_kg_url(kg_type)
    sparql = SPARQLWrapper(kg_url)
    if kg_type == "total_eb":
        query = """
            PREFIX eb: <https://w3id.org/eb#>
            SELECT ?num ?title ?part ?metsXML ?volumeId ?permanentURL ?numberOfPages ?letters WHERE {
               %s eb:number ?num ;
                  eb:title ?title;
                  eb:metsXML ?metsXML;
                  eb:volumeId ?volumeId;
                  eb:permanentURL ?permanentURL;
                  eb:numberOfPages ?numberOfPages;
                  eb:letters ?letters.
               OPTIONAL {%s eb:part ?part. }      
            }
            """ % (uri, uri)
    else:
        query = """
            PREFIX nls: <https://w3id.org/nls#>
            SELECT ?num ?title ?part ?metsXML ?volumeId ?permanentURL ?numberOfPages WHERE {
               %s nls:number ?num ;
                  nls:title ?title;
                  nls:metsXML ?metsXML;
                  nls:volumeId ?volumeId;
                  nls:permanentURL ?permanentURL;
                  nls:numberOfPages ?numberOfPages.
               OPTIONAL {%s nls:part ?part. }      
            }
            """ % (uri, uri)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r = {}
    for r in results["results"]["bindings"]:
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
    data = {}
    ###### NUM ARTICLES
    query = """
          PREFIX eb: <https://w3id.org/eb#>
          SELECT (COUNT (DISTINCT ?t) as ?count)
          WHERE {
          %s eb:hasPart ?t .
          ?t a eb:Article
         } 
         """ % (uri)
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    num_articles = results["results"]["bindings"][0]["count"]["value"]
    data["numOfArticles"] = num_articles

    ###### NUM TOPICS
    query1 = """
          PREFIX eb: <https://w3id.org/eb#>
          SELECT (COUNT (DISTINCT ?t) as ?count)
          WHERE {
          %s eb:hasPart ?t .
          ?t a eb:Topic 
         } 
         """ % (uri)
    sparqlW.setQuery(query1)
    sparqlW.setReturnFormat(JSON)
    results1 = sparqlW.query().convert()
    num_topics = results1["results"]["bindings"][0]["count"]["value"]
    data["numOfTopics"] = num_topics

    ###### NUM DIST ARTICLES
    query2 = """
         PREFIX eb: <https://w3id.org/eb#>
         PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
         SELECT (count (DISTINCT ?a) as ?count)
         WHERE {
            %s eb:hasPart ?b .
    	    ?b a eb:Article .
    	    ?b eb:name ?a.
        }
        """ % (uri)
    sparqlW.setQuery(query2)
    sparqlW.setReturnFormat(JSON)
    results2 = sparqlW.query().convert()
    num_dist_articles = results2["results"]["bindings"][0]["count"]["value"]
    data["NumOfDistinctArticles"] = num_dist_articles

    ###### NUM DIST TOPICS
    query3 = """
       PREFIX eb: <https://w3id.org/eb#>
       PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
       SELECT (count (DISTINCT ?a) as ?count)
       WHERE {
            %s eb:hasPart ?b .
    	    ?b a eb:Topic .
    	    ?b eb:name ?a.
      }
      """ % (uri)
    sparqlW.setQuery(query3)
    sparqlW.setReturnFormat(JSON)
    results3 = sparqlW.query().convert()
    num_dist_topics = results3["results"]["bindings"][0]["count"]["value"]
    data["NumOfDistinctTopics"] = num_dist_topics
    return data


def get_document(uri):
    sparql = SPARQLWrapper(eb_url)
    query = """
    PREFIX eb: <https://w3id.org/eb#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?definition ?term ?year ?enum ?vnum
        WHERE {{
            %s a eb:Article ;
               eb:name ?term ;
               eb:definition ?definition . 
            ?v eb:hasPart %s.
            ?v eb:number ?vnum.
            ?e eb:hasPart ?v.
            ?e eb:publicationYear ?year.
            ?e eb:number ?enum.
            }
            UNION {
            %s a eb:Topic ;
              eb:name ?term ; 
              eb:definition ?definition . 
            ?v eb:hasPart %s.
            ?v eb:number ?vnum.
            ?e eb:hasPart ?v.
            ?e eb:publicationYear ?year.
            ?e eb:number ?enum.
            }
       } 
    """ % (uri, uri, uri, uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    term = results["results"]["bindings"][0]["term"]["value"]
    definition = results["results"]["bindings"][0]["definition"]["value"]
    enum = results["results"]["bindings"][0]["enum"]["value"]
    year = results["results"]["bindings"][0]["year"]["value"]
    vnum = results["results"]["bindings"][0]["vnum"]["value"]
    return term, definition, enum, year, vnum
