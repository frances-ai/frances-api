#####
#This script creates the following txt files - everything regarding TERMS!! :
#- documents_total_ed.txt: it only has the definition of each article. --> terms_definitions.txt
#- terms_info_total_ed.txt: it only has the article, edition number, the year, the volume number, the part number (optional), and letter --> terms_details.txt
#- uris_total_ed.txt: it only has the uri of each article --> terms_uris.txt
####

import yaml
import matplotlib.pyplot as plt
import numpy as np
import collections
import matplotlib as mpl
from nltk import sent_tokenize
import pickle

import networkx as nx
import matplotlib.pyplot as plt
import rdflib
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx
import matplotlib.pyplot as pl
from rdflib import Graph, ConjunctiveGraph, Namespace, Literal
from rdflib.plugins.sparql import prepareQuery
import os
import networkx as nx
import matplotlib.pyplot as plt
from SPARQLWrapper import SPARQLWrapper, JSON

def get_document(uri):
    uri="<"+uri+">"
    sparql = SPARQLWrapper("http://localhost:3030/total_eb/sparql")
    query="""
    PREFIX eb: <https://w3id.org/eb#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?definition ?term
        WHERE {{
            %s a eb:Article ;
               eb:name ?term ;
               eb:definition ?definition . 
            }
            UNION {
            %s a eb:Topic ;
              eb:name ?term ; 
              eb:definition ?definition . 
            }
       } 
    """ %(uri, uri)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    term = results["results"]["bindings"][0]["term"]["value"]
    definition=results["results"]["bindings"][0]["definition"]["value"]
    return term, definition

sparql = SPARQLWrapper("http://35.228.63.82:3030/eb1/sparql")
query="""
PREFIX eb: <https://w3id.org/eb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?definition ?uri ?term ?vnum ?year ?enum ?letters ?part
        WHERE {{
    	?uri a eb:Article .
    	?uri eb:name ?term .
        ?uri eb:definition ?definition . 
        ?v eb:hasPart ?uri.
        ?v eb:number ?vnum.
        ?v eb:letters ?letters .
        ?e eb:hasPart ?v.
        ?e eb:publicationYear ?year.
        ?e eb:number ?enum.
        OPTIONAL {?v eb:part ?part; }
        }
  		UNION {
    	?uri a eb:Topic .
    	?uri eb:name ?term . 
        ?uri eb:definition ?definition .
        ?v eb:hasPart ?uri.
        ?v eb:number ?vnum.
        ?v eb:letters ?letters .
        ?e eb:hasPart ?v.
        ?e eb:publicationYear ?year.
        ?e eb:number ?enum.
        OPTIONAL {?v eb:part ?part; }
        
        }

   } 
""" 
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
documents=[]
terms_info=[]
uris=[]
for r in results["results"]["bindings"]:
    documents.append(r["definition"]["value"])
    uris.append(r["uri"]["value"])
    if "part" in r:
        terms_info.append([r["term"]["value"], r["enum"]["value"], r["year"]["value"], r["part"]["value"], r["vnum"]["value"], r["letters"]["value"]])
    else:
        terms_info.append([r["term"]["value"], r["enum"]["value"], r["year"]["value"], "" , r["vnum"]["value"], r["letters"]["value"]])

with open('terms_definitions.txt', 'wb') as fp:
    pickle.dump(documents, fp)
    
with open('terms_details.txt', 'wb') as fp2:
    pickle.dump(terms_info, fp2)
    
with open('terms_uris.txt', 'wb') as fp3:
    pickle.dump(uris, fp3)
