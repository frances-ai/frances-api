import pickle
import os, yaml
from .defoe_query_utils import preprocess_word, parse_preprocess_word_type
from ..flask_config import DefaultFlaskConfig


import numpy as np
import json

import re
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

NON_AZ_REGEXP = re.compile("[^a-z]")

stop_words = set(stopwords.words('english'))


def get_word_frequencies(text):
    words = word_tokenize(text)
    words = [word for word in words if word not in stop_words and word.isalnum()]
    word_frequencies = Counter(words)
    return word_frequencies


def normalize(word):
    """
    Normalize a word by converting it to lower-case and removing all
    characters that are not 'a',...,'z'.

    :param word: Word to normalize
    :type word: str or unicode
    :return: normalized word
    :rtype word: str or unicode
    """
    return re.sub(NON_AZ_REGEXP, '', word.lower())


def normalize_text(text):
    all_words = text.split()
    all_normalised_words = []
    for word in all_words:
        all_normalised_words.append(normalize(word))
    return ' '.join(all_normalised_words)


def get_kg_type(collection, source_provider="NLS"):
    return DefaultFlaskConfig.KG_TYPES_MAP[collection][source_provider]


def get_kg_url(kg_type):
    kg_base_url = DefaultFlaskConfig.KG_BASE_URL
    return kg_base_url + kg_type + "/sparql"


###
def load_data(input_path_embed, file_name):
    with open(os.path.join(input_path_embed, file_name), 'rb') as fp:
        data = pickle.load(fp)
    return data


def preprocess_lexicon(data_file, preprocess="normalize"):
    keysentences = []
    preprocess_type = parse_preprocess_word_type(preprocess)
    with open(data_file, 'r') as f:
        for keysentence in list(f):
            k_split = keysentence.split()
            sentence_word = [preprocess_word(word, preprocess_type) for word in k_split]
            sentence_norm = ''
            for word in sentence_word:
                if sentence_norm == '':
                    sentence_norm = word
                else:
                    sentence_norm += " " + word
            keysentences.append(sentence_norm)
    return keysentences


def dict_defoe_queries():
    defoe_q = {}
    defoe_q["frequency_keysearch_by_year"] = "frequency_keysearch_by_year"
    defoe_q["publication_normalized"] = "publication_normalized"
    defoe_q["uris_keysearch"] = "uris_keysearch"
    defoe_q["snippet_keysearch_by_year"] = "snippet_keysearch_by_year"
    defoe_q["fulltext_keysearch_by_year"] = "fulltext_keysearch_by_year"
    defoe_q["geoparser_by_year"] = "geoparser_by_year"
    defoe_q["frequency-distribution"] = "frequency-distribution"
    defoe_q["lexicon-diversity"] = "lexicon-diversity"
    defoe_q["person_entity_recognition"] = "person_entity_recognition"
    return defoe_q


def read_results(results_file):
    with open(results_file, "r") as stream:
        results = yaml.safe_load(stream)
    return results


def freq_count(results):
    freq_count = {}
    for year in results:
        for i in results[year]:
            if i[0] not in freq_count:
                freq_count[i[0]] = {}
                freq_count[i[0]][year] = i[1]

            else:
                if year not in freq_count[i[0]]:
                    freq_count[i[0]][year] = i[1]
                else:
                    freq_count[i[0]][year] += i[1]
    return freq_count


def pagination_to_dict(p):
    return {
        "page": p.page,
        "total": p.total,
        "perPage": p.per_page,
        "search": p.search,
    }


def sanitize_results(results):
    sanitized = {}
    for key, val in results.items():
        sanitized[key] = sanitize_array(val)
    return sanitized


def sanitize_array(items):
    sanitized = []
    for value in items:
        if type(value) is np.float32:
            # convert numpy float to python float
            sanitized.append(value.item())
            continue
        sanitized.append(value)
    return sanitized


def figure_to_dict(fig):
    if fig is None:
        return None
    # hack to get Figure as dict
    str_data = fig.to_json()
    dict_data = json.loads(str_data)
    return dict_data
