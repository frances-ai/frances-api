from SPARQLWrapper import SPARQLWrapper, RDF, JSON
import requests
import traceback

sparqlW = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
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


def describe_resource(uri=None):
   sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
   query="""
   PREFIX eb: <https://w3id.org/eb#>
   DESCRIBE %s 
   """ % (uri)
   sparql.setQuery(query)
   results = sparql.query().convert()
   clear_r=[]
   for s,p,o in results.triples((None, None, None)):
       data={}
       sub=str(s)
       if "#" in sub:
           sub=sub.split("#")[1]
           sub="eb:"+sub
       data["subject"]=sub
       pred=str(p)
       if "#" in pred:
           pred=pred.split("#")[1]
           pred="eb:"+pred
       data["predicate"]=pred
       obj=str(o)
       if "#" in obj:
           obj=obj.split("#")[1]
           obj="eb:"+obj
       
       if len(obj)>80:
          obj=obj[0:80]
          obj=obj+"... CONTINUE"

       data["object"]=obj
       clear_r.append(data)

   startsAtPage="-1"
   endsAtPage="-2"

   for i in range(0, len(clear_r)):
       if "startsAtPage" in clear_r[i]["predicate"]:
           startsAtPage= clear_r[i]["object"]
       if "endsAtPage" in clear_r[i]["predicate"]:
           endsAtPage= clear_r[i]["object"]
           endsAtPageIndex =i

 
   if startsAtPage == endsAtPage:
       clear_r.pop(endsAtPageIndex)
   return clear_r



def get_vol_by_vol_uri(uri):
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query="""
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?vnum ?letters ?part WHERE {
       %s eb:number ?vnum ;
          eb:letters ?letters .
           OPTIONAL {%s eb:part ?part; }
       
    
    } """ % (uri, uri)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    r=results["results"]["bindings"][0]
    if "part" in r:
       data= r["vnum"]["value"]+ " "+ r["letters"]["value"]+ "Part "+ r["part"]["value"]
    else:
       data= r["vnum"]["value"]+ " "+ r["letters"]["value"]
    return data

def get_volumes(uri):
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query="""
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?v ?vnum ?part ?letters WHERE {
       %s eb:hasPart ?v .
       ?v eb:number ?vnum ; 
          eb:letters ?letters .
          OPTIONAL {?v eb:part ?part; }
    } 
    """ % (uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    r=results["results"]["bindings"]
    clean_r={}
    for i in r:
       if "part" in i:
           clean_r[i["v"]["value"]]= [int(i["vnum"]["value"]), i["vnum"]["value"]+ " "+ i["letters"]["value"]+ "Part "+ i["part"]["value"]]
       else:
           clean_r[i["v"]["value"]]= [int(i["vnum"]["value"]), i["vnum"]["value"]+ " "+ i["letters"]["value"]]
   
    return clean_r



def get_editions():
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query1="""
    PREFIX eb: <https://w3id.org/eb#>
    SELECT ?enum ?e ?y WHERE {
           ?e a eb:Edition ;
                eb:number ?enum ;
                eb:publicationYear ?y.
               
        }"""
    query = query1
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r={}
    for r in results["results"]["bindings"]:
        clean_r[r["e"]["value"]]="Edition " + r["enum"]["value"]+ " Year "+r["y"]["value"]
    clean_r['https://w3id.org/eb/i/Edition/9910796343804340']='Sup. Edition 3 1801' 
    return clean_r


def get_numberOfVolumes(uri):
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query="""
    PREFIX eb: <https://w3id.org/eb#>
    SELECT (COUNT (DISTINCT ?v) as ?count)
        WHERE {
            %s eb:hasPart ?v.
    	    ?v ?b ?c
    }
    """ % (uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"][0]["count"]["value"]


def get_editions_details(uri=None):
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    if not uri:
       uri="<https://w3id.org/eb/i/Edition/992277653804341>"
    query="""
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
    clean_r={}
    for r in results["results"]["bindings"]:
        clean_r["Year"]=r["publicationYear"]["value"]
        clean_r["Edition Number"]=r["num"]["value"]
        clean_r["Edition URI"]=uri
        clean_r["Edition Title"]=r["title"]["value"]
        if "subtitle" in r:
            clean_r["Edition Subtitle"]=r["subtitle"]["value"]
        clean_r["Printed at"]=r["printedAt"]["value"]
        clean_r["Physical Description"]=r["physicalDescription"]["value"]
        clean_r["MMSID"]=r["mmsid"]["value"]
        clean_r["Shelf Locator"]=r["shelfLocator"]["value"]
        clean_r["Genre"]=r["genre"]["value"]
        clean_r["Language"]="English"
        clean_r["Number of Volumes"]=get_numberOfVolumes(uri)

    return clean_r

def get_volume_details(uri=None):
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query="""
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
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    clean_r={}
    for r in results["results"]["bindings"]:
        clean_r["Volume Number"]=r["num"]["value"]
        clean_r["Volume URI"]=uri
        clean_r["Volume Title"]=r["title"]["value"]
        clean_r["Volume Letters"]=r["letters"]["value"]
        if "part" in r:
            clean_r["Volume Part"]=r["part"]["value"]
        clean_r["Volume Permanent URL"]= r["permanentURL"]["value"]
        clean_r["Volume Number of Pages"]=r["numberOfPages"]["value"]
    return clean_r



def get_definition(term=None, documents=None, uris=None):
    term=term.upper()
    query1="""
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
   """ %(term, term)
    query = query1
    sparqlW.setQuery(query)
    sparqlW.setReturnFormat(JSON)
    results = sparqlW.query().convert()
    clean_r={}
    list_terms={}
    cont=0
    for r in results["results"]["bindings"]:
        permanentURL= r["permanentURL"]["value"]
        startPermanentURL = permanentURL+"#?c=0&m=0&s=0&cv="+r["spnum"]["value"]
        endPermanentURL = permanentURL+"#?c=0&m=0&s=0&cv="+r["epnum"]["value"]
   
        if "Article" in r["b"]["value"]:
            term_type="Article"
            definition=r["definition"]["value"]
        else:
            try:
                term_type="Topic"
                indice=uris.index(r["b"]["value"])
                definition="Summary: "+ documents[indice]
            except:
                term_type="Topic"
                definition=r["definition"]["value"][0:100]

        if "rn" in r:
            if r["b"]["value"] not in list_terms:
                list_terms[r["b"]["value"]]=[]
            if r["rn"]["value"] not in list_terms[r["b"]["value"]]:
                list_terms[r["b"]["value"]].append(r["rn"]["value"])
            clean_r[r["b"]["value"]]=[r["year"]["value"], r["enum"]["value"], r["vnum"]["value"], [startPermanentURL, r["spnum"]["value"]], [endPermanentURL,r["epnum"]["value"]], term_type, definition, list_terms[r["b"]["value"]]]
        else:
            clean_r[r["b"]["value"]]=[r["year"]["value"], r["enum"]["value"], r["vnum"]["value"], [startPermanentURL, r["spnum"]["value"]], [endPermanentURL,r["epnum"]["value"]], term_type, definition, []]
    return clean_r

def get_vol_statistics(uri):
    data={}
    ###### NUM ARTICLES
    query="""
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
    num_articles=results["results"]["bindings"][0]["count"]["value"]
    data["Number of Articles"]=num_articles

    ###### NUM TOPICS
    query1="""
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
    num_topics=results1["results"]["bindings"][0]["count"]["value"]
    data["Number of Topics"] = num_topics

    ###### NUM DIST ARTICLES
    query2="""
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
    num_dist_articles= results2["results"]["bindings"][0]["count"]["value"]
    data["Number of Distinct Articles"] = num_dist_articles


    ###### NUM DIST TOPICS
    query3="""
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
    num_dist_topics= results3["results"]["bindings"][0]["count"]["value"]
    data["Number of Distinct Topics"] = num_dist_topics
    return data
            
def get_document(uri):
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query="""
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
    """ %(uri, uri, uri, uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    term = results["results"]["bindings"][0]["term"]["value"]
    definition=results["results"]["bindings"][0]["definition"]["value"]
    enum=results["results"]["bindings"][0]["enum"]["value"]
    year=results["results"]["bindings"][0]["year"]["value"]
    vnum=results["results"]["bindings"][0]["vnum"]["value"]
    return term, definition, enum, year, vnum
