#!/usr/bin/env python
# coding: utf-8

# # Merging EB terms-  NLS -  Encyclopaedia Britannica
# 

# ### Loading the necessary libraries



import yaml
import numpy as np
import collections
import string
import copy
import sys

import pandas as pd
from yaml import safe_load
from pandas.io.json import json_normalize
from difflib import SequenceMatcher


# ### Functions


def read_query_results(filename):
    with open('../results_NLS/'+filename, 'r') as f:
        query_results = safe_load(f)
    return query_results



def write_query_results(filename, results):
    with open('../results_NLS/'+filename, 'w') as f:
        documents = yaml.dump(results, f)


def similar(a, b):
    a=a.lower()
    b=b.lower()
    return SequenceMatcher(None, a, b).ratio()



def most_frequent(List):
    return max(set(List), key = List.count)



def check_string(term, List):
    flag = 0
    for element in List:
        if element in term:
            flag = 1
            break
    if flag == 1:
        return True
    else:
        return False



def clean_topics_terms(term):
    table = str.maketrans('', '', string.ascii_lowercase)
    return term.translate(table)






def prune_json(json_dict):
    """
    Method that given a JSON object, removes all its empty fields.
    This method simplifies the resultant JSON.
    :param json_dict input JSON file to prune
    :return JSON file removing empty values
    """
    final_dict = {}
    if not (isinstance(json_dict, dict)):
        # Ensure the element provided is a dict
        return json_dict
    else:
        for a, b in json_dict.items():
            if b or isinstance(b, bool):
                if isinstance(b, dict):
                    aux_dict = prune_json(b)
                    if aux_dict:  # Remove empty dicts
                        final_dict[a] = aux_dict
                elif isinstance(b, list):
                    aux_list = list(filter(None, [prune_json(i) for i in b]))
                    if len(aux_list) > 0:  # Remove empty lists
                        final_dict[a] = aux_list
                else:
                    final_dict[a] = b
    return final_dict


# In[13]:


def delete_entries(query_results_updated, eliminate_pages):
    new_results={}
    for edition in query_results_updated:
        new_results[edition]=[]
        for page_idx in range(0, len(query_results_updated[edition])):
            if page_idx not in eliminate_pages[edition]:
                new_results[edition].append(query_results_updated[edition][page_idx])
    return new_results



def deleting_adding_entries(query_results_up, eliminate_pages, create_entries):
    new_results={}
    flag = 1
    for edition in query_results_up:
        new_results[edition]=[]
        for page_idx in range(0, len(query_results_up[edition])):
            if page_idx not in eliminate_pages[edition]:
                new_results[edition].append(query_results_up[edition][page_idx])
            else:
                for new_pages in create_entries[edition][page_idx]:
                    new_results[edition].append(new_pages)
            
        
    return new_results      



def related_terms_info(related_terms):
    
    related_data=[]
    for elem in related_terms:
        if elem.isupper() or "." in elem or "," in elem:
            elem=elem.split(".")[0]
            term=elem.split(",")[0]
            if len(term)>2 and term[0].isupper() :
                m = re.search('^([0-9]+)|([IVXLCM]+)\\.?$', term)
                if m is None:
                    term_up = term.upper()
                    if term_up !="FIG" and term_up !="NUMBER" and term_up!="EXAMPLE" and term_up!="PLATE" and term_up!="FIGURE":
                        related_data.append(term_up) and term_up!="EXAMPLE" and term_up!="PLATE" and term_up!="FIGURE"
                        related_data.append(term_up)
    return related_data



def fixing_articles(query_results):
    
    create_entries={}
    eliminate_pages={}
    for edition in query_results:
        create_entries[edition]={}
        eliminate_pages[edition]=[]
        flag_p = 1
        for page_idx in range(0, len(query_results[edition])):
            element = query_results[edition][page_idx][1]
            element_page = query_results[edition][page_idx][0]
            flag = 0
            
            if element["type_page"]=="Topic" and len(element["term"])<=7:
                
                list_terms=[]
                new_entries=[]
                definition=element["definition"]
                definition_list= definition.split(" ")
                term = element["term"]
                flag = 0
                sub_elements=[]
                for word_idx in range(0, len(definition_list)):
                    word = definition_list[word_idx]
                    if word.isupper() and "," in word and len(word)>3 and "See "!= definition_list[word_idx-1] and "SEE " != definition_list[word_idx-1]:
                        sub_elements.append((word.split(",")[0],word_idx))
                        flag = 1
                        
                     
                if flag and len(sub_elements) >= 5:
                    for elem_idx in range(0, len(sub_elements)):
                        term_id = 0
                       
                        new_element={}
                        elem=sub_elements[elem_idx]
                        new_element["term"]=elem[0]
     
                        if elem_idx+1 < len(sub_elements):
                            sentence=definition_list[elem[1]+1: sub_elements[elem_idx+1][1]]
                            new_element["definition"]=' '.join(sentence)
                       
                            
                        else:
                            new_element["last_term_in_page"] = 1
                            try:
                                sentence= definition_list[elem[1]+1:][1]
                                new_element["definition"]=' '.join(sentence)
        
                            except:
                                sentence= definition_list[elem[1]:]
                                if len(sentence) > 3:
                                    new_element["definition"]=' '.join(sentence)
       
                        if "definition" in new_element and len(new_element["term"])>4:
                            
                            new_element["type_page"] = "Article" 
                            new_element["num_article_words"] = len(sentence)  
                            #### related terms ##### 
                            related_terms=[]
                            if "See " in new_element["definition"]:
                                related_terms= new_element["definition"].split("See ")[1]
                            elif "SEE " in new_element["definition"]:
                                related_terms= new_element["definition"].split("SEE ")[1]  
                            new_element["related_terms"]=related_terms_info(related_terms)
                            ####
                            
                            new_element["term_id_in_page"]=term_id 
                            new_element["archive_filename"]= element["archive_filename"]
                            new_element["header"] = element["header"]
                            new_element["model"] = element["model"]
                            new_element["num_page_words"]= element["num_page_words"]
                            new_element["num_text_unit"] = element["num_text_unit"]
                            new_element["place"] = element["place"]
                            new_element["source_text_file"] = element["source_text_file"]
                            new_element["text_unit"] = element["text_unit"]
                            new_element["text_unit_id"] = element["text_unit_id"]
                            new_element["title"] = element["title"]
                            new_element["type_archive"] = element["type_archive"]
                            new_element["year"] = element["year"]
                            new_element["end_page"] =int(element['text_unit_id'].split("Page")[1])
                            new_element["edition"] = element["edition"]
                            
                            new_entries.append(new_element)
                            list_terms.append(new_element["term"])
                            term_id += 1
                        
                if len(list_terms) > 12:
                    for i in new_entries:
                        i["num_articles"] = len(list_terms)
                    eliminate_pages[edition].append(page_idx)
                    create_entries[edition][page_idx]=[]
                    for new_d in new_entries:
                        create_entries[edition][page_idx].append([element_page, new_d])
                             
   
    new_results = deleting_adding_entries(query_results, eliminate_pages, create_entries)
    return new_results
 


def fixing_topics(query_results):
     for edition in query_results:
        for page_idx in range(0, len(query_results[edition])):
            element = query_results[edition][page_idx][1]
            if (element["num_articles"] == 1) and ((element["type_page"]=="Article") or element["type_page"]=="Mix"):
                prev_element = query_results[edition][page_idx-1][1]
                element_term = element["term"]
                if prev_element["type_page"]=="Topic":
                    element["type_page"]=="Topic"
                    element["term"]=prev_element["term"]
                    print("Moved %s to %s" %(element_term, prev_element["term"] ))
    


def merge_articles(query_results):
    eliminate_pages={}
    for edition in query_results:
        eliminate_pages[edition]=[]
        page_number_dict={}
        for page_idx in range(0, len(query_results[edition])):
            
            current_page=query_results[edition][page_idx][0]
            
            if current_page not in page_number_dict:
                page_number_dict[current_page]=page_idx
            
            element = query_results[edition][page_idx][1]
            
            ### checking the first 20 pages and transforming them to FullPages #### 
            if int(current_page) < 20:
                if element["type_page"]!="FullPage":
                    element = page2full_pages(element)
            
                next_element= query_results[edition][page_idx+1][1]
                if element["type_page"]!="FullPage" and next_element["type_page"]=="FullPage":
                    element["type_page"] = "FullPage"
            
            ###########################################        
            
            if "previous_page" in element['term']:
                current_definition= element["definition"]
                previous_page_idx= page_idx -1
                previous_page_number = current_page -1
                num_article_words=element["num_article_words"]
                related_terms=element["related_terms"]
            
                
                prev_elements = query_results[edition][previous_page_idx][1]
                if prev_elements["last_term_in_page"]:
                   
                    prev_elements["definition"]+=current_definition
                    prev_elements["num_article_words"]+=num_article_words
                    prev_elements["related_terms"]+= related_terms
                    prev_number = int(prev_elements['text_unit_id'].split("Page")[1])
                    prev_elements["end_page"] = current_page

                    if prev_number in page_number_dict: 
                        for prev_articles_idx in range(page_number_dict[prev_number], page_idx):
                       
                            if query_results[edition][prev_articles_idx][0] == prev_number:
                           
                                query_results[edition][prev_articles_idx][1]["num_page_words"]+=num_article_words

                    else:
                        print("Edition %s -ERROR page %s -" % (edition,current_page))
                    for update_element_idx in range(page_number_dict[current_page], page_idx+1):
                        if query_results[edition][update_element_idx][0] == current_page:
                            query_results[edition][update_element_idx][1]["num_page_words"]-=num_article_words
                            query_results[edition][update_element_idx][1]["num_articles"]-=1
                    
                
                eliminate_pages[edition].append(page_idx)
            else:
                element["end_page"] = current_page  
   
    new_results= delete_entries(query_results, eliminate_pages)
    
    return new_results


# In[19]:


def merge_topics(query_results):
    eliminate_pages={}
    provenance_removal={}
    freq_topics_terms={}
    merged_topics={}
    parts_string=["Part", "Fart", "Parc", "CPart", "PI"]
    for edition in query_results:
        eliminate_pages[edition]=[]
        provenance_removal[edition]=[]
        freq_topics_terms[edition]={}
        merged_topics[edition]={}
        
        page_idx = 0
        while page_idx < len(query_results[edition]):
            current_page=query_results[edition][page_idx][0]        
            element = query_results[edition][page_idx][1]

            if "Topic" in element['type_page'] and element["term"]!="" and element["term"]!=" ":
                
                if check_string(element["term"], parts_string):
                   
                    ### It means that the previous page was a topic
                    ### And we have one before and correct the error
                    page_idx = page_idx -1 
                    element = query_results[edition][page_idx][1]
                    element['type_page']="Topic"
                    
            
                term=element["term"]
                clean_term=clean_topics_terms(term)
                
                next_page_idx= page_idx + 1
                      
                if next_page_idx < len(query_results[edition]):
                    flag=0
                    tmp_idx = 0
                    for p_id in range(next_page_idx, len(query_results[edition])):
                        next_element = query_results[edition][p_id][1]
   
                        if not check_string(next_element["term"], parts_string):
                            next_term=clean_topics_terms(next_element["term"])
                        else:
                            next_term=next_element["term"]
                    
                        if similar(clean_term, next_term) > 0.72 or check_string(next_term, parts_string) or next_term in clean_term: 

                            if term not in merged_topics[edition]:
                                merged_topics[edition][clean_term]=[]
                        
                            if not check_string(next_term, parts_string) :
                                 merged_topics[edition][clean_term].append(next_term)
                         
                            element["definition"]+=next_element["definition"]
                            element["num_article_words"]+=next_element["num_article_words"]
                            element["num_page_words"]+=next_element["num_page_words"]                  
                            element["related_terms"]+= next_element["related_terms"]
                            element["end_page"] = int(next_element['text_unit_id'].split("Page")[1])
                            provenance_removal[edition].append(element["end_page"])

                            eliminate_pages[edition].append(p_id)
                            tmp_idx= p_id + 1
                        else:
                            flag = 1
                            break
                  
        
                    if flag:
                         page_idx= p_id
                    
                    else:
                        page_idx = tmp_idx
                        
                 
                    if clean_term in merged_topics[edition]:
                       
                        if merged_topics[edition][clean_term]:
                            freq_term=most_frequent(merged_topics[edition][clean_term])
                            freq_topics_terms[edition][term]=freq_term
                            element["term"]=freq_term
                        else:
                            element["term"]=clean_term
                    else:
                        element["term"]=clean_term
                    
                else:
                    page_idx = next_page_idx
                    
                
               
            else:
                page_idx += 1
           
    #for ed in provenance_removal:
    #    print("ED:%s -- removing the following pages %s" %(ed, provenance_removal[ed]))
    new_results= delete_entries(query_results, eliminate_pages)
    
    return new_results, merged_topics, freq_topics_terms


# In[20]:


def merge_topics_refine(query_results):
    
    topics_editions={}
    eliminate_pages={}
    merged_topics_refine={}
    provenance_removal={}
    for edition in query_results:
        eliminate_pages[edition]=[]
        provenance_removal[edition]=[]
        topics_editions[edition]={}
        merged_topics_refine[edition]=[]
        page_idx = 0
        character="A"
        while page_idx < len(query_results[edition]):
            
            element = query_results[edition][page_idx][1]
            term = element["term"]
           
            
            if "Topic" in element['type_page'] and term!="" and term!=" " and term[0] >= character:
                character=term[0]
                if term not in topics_editions[edition]:
                    topics_editions[edition][term]=page_idx
                    #print("NEW: Topic --%s-- - Page: %s "%(term, topics_editions[edition][term]))
                else:
                    start_page_idx=topics_editions[edition][term]
                    first_element = query_results[edition][start_page_idx][1]
                    
                    first_element["definition"]+=element["definition"]
                    first_element["num_article_words"]+=element["num_article_words"]
                    first_element["num_page_words"]+=element["num_page_words"]                  
                    first_element["related_terms"]+= element["related_terms"]
                    first_element["end_page"] = int(element['text_unit_id'].split("Page")[1])
                    provenance_removal[edition].append(first_element["end_page"])
                    merged_topics_refine[edition].append(term)
                    eliminate_pages[edition].append(page_idx)
                    
                
            
            page_idx += 1
            if term:
                character=term[0]
        
    new_results= delete_entries(query_results, eliminate_pages)
    
    return new_results, provenance_removal, merged_topics_refine



def page2full_pages(element):
    


    term = element["term"]
    header = element["header"]
    type_page = element["type_page"]
    
    if ("PREFACE" in term) or ("PREFACE" in header):
        term = "PREFACE"
        header = "PREFACE"
        type_page="FullPage"
    
    elif ("Plate" in term) or ("Plafr" in term) or ("Elate" in term) or ("Tlafe" in term):
        header = "Plate"
        term = "Plate"
        type_page = "FullPage"
        
    elif ("Plate" in header) or ("Plafr" in header) or ("Elate" in header) or ("Tlafe" in header):
        header = "Plate"
        term = "Plate"
        type_page = "FullPage"
        
    elif ("ARTSandSCI" in term) or ("ARTSandSCI" in header):
        header = "FrontPage"
        term = "FrontPage"
        type_page="FullPage"

        
    elif "ERRATA" in term or ("ERRATA" in header):
        header = "ERRATA"
        term = "ERRATA"
        type_page="FullPage"
        
   
    elif (" LISTofAUTHORSc" in term) or ("LISTofAUTHORS" in term) or ("ListofAUTHORS" in term) or ("listofAuthors" in term) or ("ListOfAuthors" in term) or ("listofauthors" in term):
        header = "AuthorList"
        term = "AuthorList"
        type_page="FullPage"
        
    elif ("LISTofAUTHORSc" in header) or ("LISTofAUTHORS" in header) or ("ListofAUTHORS" in header) or ("listofAuthors" in header) or ("ListOfAuthors" in header) or ("listofauthors" in header):
        header = "AuthorList"
        term = "AuthorList"
        type_page="FullPage"
        
       
    
    element["term"] = term
    element["header"] = header
    element["type_page"] = type_page
    return element


# ### 1. Reading data

# Here we are going to take the output of the defoe files, and we are going to merge the terms that splitted across pages. 
# 
# The next line takes time!

# In[22]:


def main():
    print(sys.argv, len(sys.argv))

    file_name = sys.argv[1]
    query_results=read_query_results(file_name)

    dc_results = copy.deepcopy(query_results)

    query_results_articles = merge_articles(dc_results)

    articles_refined=fixing_articles(query_results_articles)

    fixing_topics(articles_refined)

    topics_refined, merged_topics, freq_topics_terms =merge_topics(articles_refined)

    final_refine, provenance_removal,merged_topics_refine =merge_topics_refine(topics_refined)

    write_query_results(file_name+"_updated", final_refine)


if __name__ == "__main__":
    main()