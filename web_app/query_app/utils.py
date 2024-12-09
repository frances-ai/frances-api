import re

NON_AZ_REGEXP = re.compile("[^a-z]")


def get_precomputed_name(collection_name, model_name, source, query_name):
    collection_name = collection_name.lower()
    collection_id_name = re.sub(NON_AZ_REGEXP, '', collection_name)
    pre_computed_name = model_name + "_" + collection_id_name + "_" + source + '_' + query_name
    return pre_computed_name