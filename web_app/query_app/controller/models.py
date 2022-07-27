import json
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from .utils import load_data


class ModelsRepository:
  def __init__(self, config):
    # Models
    self.text_embeddings = np.load(config.models_path + '/embeddings_mpnet.npy')
    self.topic_model = BERTopic.load(config.models_path + '/BerTopic_Model_mpnet') 
    self.model = SentenceTransformer('all-mpnet-base-v2')

    # Terms Info
    self.documents=load_data(config.models_path, 'terms_definitions_final.txt')
    self.terms_info=load_data(config.models_path, 'terms_details.txt')
    self.uris=load_data(config.models_path, 'terms_uris.txt')

    # Terms Similarity
    self.paraphrases=load_data(config.models_path, 'paraphrases_mpnet.txt')
    self.paraphrases_index_first=load_data(config.models_path, 'paraphrases_index_first.txt')
    self.paraphrases_index_second=load_data(config.models_path, 'paraphrases_index_second.txt')

    # LDA Topic Modelling
    ### lda topics_mpnet[-1] --> 5: Just the number of the lda topic per term
    self.topics=load_data(config.models_path, 'lda_topics_mpnet.txt')
    ## The names of topics: t_names -->['1_lat_miles_long_town', '0_the_to_and_is'
    self.t_names=load_data(config.models_path, 'lda_t_names_mpnet.txt')

    #### The topic of each document: topics_names ['1_lat_miles_long_town', '0_the_to_and_is', '79_church_romiffi_idol_deum', '11_poetry_verse_verses_poem', '0_the_to_and_is', '0_the_to_and_is', '0_the_to_and_is', '0_the_to_and_is', '6_measure_weight_inches_containing', '1_lat_miles_long_town']
    self.topics_names=load_data(config.models_path, 'lda_topics_names_mpnet.txt')

    # Sentiment and Clean Terms
    self.sentiment_terms=load_data(config.models_path,'terms_sentiments.txt')
    self.clean_documents=load_data(config.models_path, 'clean_terms_definitions_final.txt')
