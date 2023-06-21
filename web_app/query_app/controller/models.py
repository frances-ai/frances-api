import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from .utils import load_data
from web_app.query_app.flask_config import DefaultFlaskConfig

models_path = DefaultFlaskConfig.MODELS_FOLDER


class ModelsRepository:
    # Models
    text_embeddings = np.load(models_path + '/embeddings_mpnet.npy')
    topic_model = BERTopic.load(models_path + '/BerTopic_Model_mpnet')
    model = SentenceTransformer('all-mpnet-base-v2')

    # Terms Info
    documents = load_data(models_path, 'terms_definitions_final.txt')
    terms_info = load_data(models_path, 'terms_details.txt')
    uris = load_data(models_path, 'terms_uris.txt')

    # Terms Similarity
    paraphrases = load_data(models_path, 'paraphrases_mpnet.txt')
    paraphrases_index_first = load_data(models_path, 'paraphrases_index_first.txt')
    paraphrases_index_second = load_data(models_path, 'paraphrases_index_second.txt')

    # LDA Topic Modelling
    # lda topics_mpnet[-1] --> 5: Just the number of the lda topic per term
    topics = load_data(models_path, 'lda_topics_mpnet.txt')
    # The names of topics: t_names -->['1_lat_miles_long_town', '0_the_to_and_is'
    t_names = load_data(models_path, 'lda_t_names_mpnet.txt')

    # The topic of each document: topics_names ['1_lat_miles_long_town', '0_the_to_and_is', '79_church_romiffi_idol_deum', '11_poetry_verse_verses_poem', '0_the_to_and_is', '0_the_to_and_is', '0_the_to_and_is', '0_the_to_and_is', '6_measure_weight_inches_containing', '1_lat_miles_long_town']
    topics_names = load_data(models_path, 'lda_topics_names_mpnet.txt')

    # Sentiment and Clean Terms
    sentiment_terms = load_data(models_path, 'terms_sentiments.txt')
    clean_documents = load_data(models_path, 'clean_terms_definitions_final.txt')
