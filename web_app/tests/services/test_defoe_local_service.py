import unittest
from web_app.query_app.service.defoe_service import local_defoe_service
from web_app.query_app.flask_config import DefaultFlaskConfig


class TestDefoeLocalService(unittest.TestCase):

    def setUp(self):
        channel = "localhost:5052"
        self.service = local_defoe_service.LocalDefoeService(channel)
        self.model_name = 'hto'
        self.endpoint = 'http://query.frances-ai.com/hto'
        self.web_app_path = str(DefaultFlaskConfig.WEB_APP_DIR)

    def test_hto_publication_normalisation_query(self):
        query_name = 'publication_normalized'
        query_config = {'collection': 'Encyclopaedia Britannica',
                        'source': 'NLS'}
        result_file_path = self.web_app_path + "/hto_eb_nls_publication_normalisation.yml"
        job_id = 'hto_eb_nls_publication_normalisation'
        self.service.submit_job(job_id, self.model_name, query_name, self.endpoint, query_config, result_file_path)
        print(self.service.get_status(job_id))

    def test_hto_lexical_diversity_query(self):
        query_name = 'lexical_diversity'
        query_config = {'collection': 'Encyclopaedia Britannica',
                        'level': "volume",
                        'source': 'NLS'}
        result_file_path = self.web_app_path + "hto_eb_nls_ld.yml"

        job_id = 'hto_eb_nls_ld'

        self.service.submit_job(job_id, self.model_name, query_name, self.endpoint, query_config, result_file_path)

        print(self.service.get_status(job_id))

    def test_hto_frequency_distribution_query(self):
        query_name = 'frequency_distribution'
        query_config = {'collection': 'Encyclopaedia Britannica',
                        'level': "edition",
                        'source': 'NLS'}
        result_file_path = self.web_app_path + "/hto_eb_edition_nls_freqDist.yml"

        job_id = 'hto_eb_nls_freq_dist'

        self.service.submit_job(job_id, self.model_name, query_name, self.endpoint, query_config, result_file_path)
        print(result_file_path)
        print(self.service.get_status(job_id))

    def test_hto_person_entity_recognition_query(self):
        query_name = 'person_entity_recognition'
        query_config = {'collection': 'Chapbooks printed in Scotland',
                        'level': "collection",
                        'source': 'NLS'}
        result_file_path = self.web_app_path + "/hto_chapbooks_nls_persons.yml"

        job_id = 'hto_chapbook_nls_persons'

        self.service.submit_job(job_id, self.model_name, query_name, self.endpoint, query_config, result_file_path)

        print(self.service.get_status(job_id))
