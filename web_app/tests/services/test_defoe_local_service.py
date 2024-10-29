import unittest
from web_app.query_app.service.defoe_service import local_defoe_service


class TestDefoeLocalService(unittest.TestCase):
    def test_hto_publication_normalisation_query(self):
        channel = "localhost:5052"
        service = local_defoe_service.LocalDefoeService(channel)
        model_name = 'hto'
        endpoint = 'http://query.frances-ai.com/hto'
        query_name = 'frequency_keysearch_by_year'
        # query_name = 'snippet_keysearch_by_year'
        #query_name = 'publication_normalized'
        query_config = {'collection': 'Encyclopaedia Britannica',
                        "data": "/Users/lilinyu/Documents/frances-ai/defoe_lib/queries/animal.txt",
                        'source': 'NLS'}
        result_file_path = "/Users/lilinyu/Documents/frances-ai/frances-api/hto_eb_nls_frequency.yml"

        # query_name = 'geoparser_by_year'
        # query_config = {'preprocess': 'none', 'target_sentences': '', 'hit_count': 'term', 'data': '/Users/ly40/Documents/frances-ai/defoe_lib/queries/scots.txt', 'gazetteer': 'geonames', 'start_year': '1770', 'end_year': '1772', 'kg_type': 'chapbooks_scotland', 'window': 'None'}
        # result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/scots_geoparser.yml"
        job_id = 'hto_eb_nls_publication_normalisation'

        # query_name = 'publication_normalized'

        service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

        # another_service = DefoeService(main_python_file_uri, python_file_uris, cluster)
        # print(DefoeService.preComputedJobID)
        print(service.get_status(job_id))

    def test_hto_lexical_diversity_query(self):
        channel = "localhost:5052"
        service = local_defoe_service.LocalDefoeService(channel)
        model_name = 'hto'
        endpoint = 'http://query.frances-ai.com/hto'
        query_name = 'lexical_diversity'
        # query_name = 'snippet_keysearch_by_year'
        #query_name = 'publication_normalized'
        query_config = {'collection': 'Encyclopaedia Britannica',
                        'level': "volume",
                        'source': 'NLS'}
        result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/hto_eb_nls_ld.yml"

        job_id = 'hto_eb_nls_ld'

        service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

        print(service.get_status(job_id))

    def test_hto_frequency_distribution_query(self):
        channel = "localhost:5052"
        service = local_defoe_service.LocalDefoeService(channel)
        model_name = 'hto'
        endpoint = 'http://query.frances-ai.com/hto'
        query_name = 'frequency_distribution'
        query_config = {'collection': 'Encyclopaedia Britannica',
                        'level': "edition",
                        'source': 'NLS'}
        result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/hto_eb_edition_nls_freqDist.yml"

        job_id = 'hto_eb_nls_freq_dist'

        service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

        print(service.get_status(job_id))

    def test_hto_person_entity_recognition_query(self):
        channel = "localhost:5052"
        service = local_defoe_service.LocalDefoeService(channel)
        model_name = 'hto'
        endpoint = 'http://query.frances-ai.com/hto'
        query_name = 'person_entity_recognition'
        query_config = {'collection': 'Chapbooks printed in Scotland',
                        'level': "collection",
                        'source': 'NLS'}
        result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/hto_chapbooks_nls_persons.yml"

        job_id = 'hto_chapbook_nls_persons'

        service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

        print(service.get_status(job_id))
