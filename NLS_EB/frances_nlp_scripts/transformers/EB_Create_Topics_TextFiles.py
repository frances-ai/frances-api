#####
#This script creates the following txt files - everything regarding TOPICS!! :
#- topics_documents_total_ed.txt: it only has the definition of each topic. --> topics_definitions.txt
#- topics_info_total_ed.txt: it only has the topic, edition number, the year, the volume number, the part number (optional), and letter --> topics_details.txt
#- topics_uris_total_ed.txt: it only has the uri of each topic --> topics_uris.txt
#- indices_[1-8].txt: create a list of indices, to know which years correspond to each edition.

#### It crates


import yaml
import numpy as np
import collections
import matplotlib as mpl
import pickle

import networkx as nx
import rdflib
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
from rdflib import Graph, ConjunctiveGraph, Namespace, Literal
from rdflib.plugins.sparql import prepareQuery
import os
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://35.228.63.82:3030/eb1/sparql")
query="""
PREFIX eb: <https://w3id.org/eb#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?definition ?uri ?term ?vnum ?year ?enum ?letters ?part
        WHERE {
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
""" 
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
topics_documents=[]
topics_info=[]
topics_uris=[]
for r in results["results"]["bindings"]:
    topics_documents.append(r["definition"]["value"])
    topics_uris.append(r["uri"]["value"])
    if "part" in r:
        topics_info.append([r["term"]["value"], r["enum"]["value"], r["year"]["value"], r["part"]["value"], r["vnum"]["value"], r["letters"]["value"]])
    else:
        topics_info.append([r["term"]["value"], r["enum"]["value"], r["year"]["value"], "" , r["vnum"]["value"], r["letters"]["value"]])

#list_years=["1771", "1773", "1778", "1797", "1801", "1810", "1815", "1823", "1842", "1853"]
#ed_years={}
#ed_year["1a"]=[1771]
#ed_year["1b"]=[1773]
#ed_year["2"]=[1778]
#ed_year["3"]=[1797, 1801, 1803]
#ed_year["4"]=[1810, 1824]
#ed_year["5"]=[1815, 1824]
#ed_year["6"]=[1823, 1824]
#ed_year["7"]=[1842]
#ed_year["8"]i=[1853]

indices_ed={}
print("Phase 1")
for i in range(0, len(topics_info)):
    ed=topics_info[i][1]
    year=topics_info[i][2]
    if ed == "1":
       year=topics_info[i][2]
       if year == "1771":
           ed_name="1_1771"
       else:
           ed_name="1_1773"

    elif ed == "0":
           ed_name="3_supplement"
    else:
        ed_name=ed
    if ed_name not in indices_ed :
        indices_ed[ed_name]=[]
    indices_ed[ed_name].append(i)

print("Phase 2")
with open('topics_definitions.txt', 'wb') as fp:
    pickle.dump(topics_documents, fp)
    
with open('topics_details.txt', 'wb') as fp2:
    pickle.dump(topics_info, fp2)
    
with open('topics_uris.txt', 'wb') as fp3:
    pickle.dump(topics_uris, fp3)
    
for ed in indices_ed:
   filename='indices_%s.txt'%(ed)
   with open(filename, 'wb') as fp4:
       pickle.dump(indices_ed[ed], fp4)
    
