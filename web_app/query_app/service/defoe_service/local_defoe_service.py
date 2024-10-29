import re

import grpc
from .defoe_pb2 import JobSubmitRequest, JobRequest
from .defoe_pb2_grpc import DefoeStub
from ...utils import get_precomputed_name

class LocalDefoeService:
    preComputedJobID = []

    @staticmethod
    def get_pre_computed_queries():
        return {
            "hto_encyclopaediabritannica_NLS_publication_normalized": "precomputedResult/hto_encyclopaediabritannica_NLS_publication_normalized.yml",
            "hto_encyclopaediabritannica_NeuSpell_publication_normalized": "precomputedResult/hto_encyclopaediabritannica_NeuSpell_publication_normalized.yml",
            "hto_encyclopaediabritannica_HQ_publication_normalized": "precomputedResult/hto_encyclopaediabritannica_HQ_publication_normalized.yml",
            "hto_chapbooksprintedinscotland_NLS_publication_normalized": "precomputedResult/hto_chapbooksprintedinscotland_NLS_publication_normalized.yml",
            "hto_gazetteersofscotland_NLS_publication_normalized": "precomputedResult/hto_gazetteersofscotland_NLS_publication_normalized.yml",
            "hto_ladiesedinburghdebatingsociety_NLS_publication_normalized": "precomputedResult/hto_ladiesedinburghdebatingsociety_NLS_publication_normalized.yml",
            "ebo_total_hq_publication_normalized": "precomputedResult/ebo_total_hq_publication_normalized.yml",
            "ebo_total_publication_normalized": "precomputedResult/ebo_total_publication_normalized.yml",
        }

    def __init__(self, channel):
        self.channel = channel

    def submit_job(self, job_id, model_name, query_name, endpoint, query_config, result_file_path):
        collection_name = query_config["collection"]
        source = query_config["source"]
        pre_computed_name = get_precomputed_name(collection_name, model_name, source, query_name)
        if pre_computed_name in LocalDefoeService.get_pre_computed_queries():
            LocalDefoeService.preComputedJobID.append(job_id)
            return job_id

        try:
            with grpc.insecure_channel(self.channel) as channel:
                stub = DefoeStub(channel)
                job_submit_request = JobSubmitRequest(job_id=job_id, model_name=model_name,
                                                      query_name=query_name, endpoint=endpoint,
                                                      query_config=query_config,
                                                      result_file_path=result_file_path)
                response = stub.submit_job(job_submit_request)
                return response.job_id

        except Exception as E:
            raise Exception(E)

    def get_status(self, job_id, is_pre_computed=False):
        if is_pre_computed:
            return {
                "state": "DONE"
            }

        try:
            with grpc.insecure_channel(self.channel) as channel:
                stub = DefoeStub(channel)
                job_request = JobRequest(job_id=job_id)
                response = stub.get_job(job_request)
                print(response)
                if response.error and response.error != "":
                    return {
                        "state": response.state,
                        "details": response.error
                    }
                return {
                    "state": response.state
                }
        except Exception as E:
            print('exception')
            raise Exception(E)

    def cancel_job(self, job_id):
        # TODO Implement cancel job in local defoe service
        pass


if __name__ == "__main__":
    channel = "localhost:5052"
    service = LocalDefoeService(channel)

    model_name = 'hto'
    endpoint = 'http://127.0.0.1:3030/hto'
    #query_name = 'frequency_keysearch_by_year'
    #query_name = 'snippet_keysearch_by_year'
    query_name = 'publication_normalized'
    query_config = {'collection': 'Chapbooks printed in Scotland', 'source': 'NLS'}
    result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/hto_nls_publication_normalisation.yml"

    #query_name = 'geoparser_by_year'
    #query_config = {'preprocess': 'none', 'target_sentences': '', 'hit_count': 'term', 'data': '/Users/ly40/Documents/frances-ai/defoe_lib/queries/scots.txt', 'gazetteer': 'geonames', 'start_year': '1770', 'end_year': '1772', 'kg_type': 'chapbooks_scotland', 'window': 'None'}
    #result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/scots_geoparser.yml"
    job_id = 'hto_nls_chapbooks_publication_normalisation'

    #query_name = 'publication_normalized'

    service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

    # another_service = DefoeService(main_python_file_uri, python_file_uris, cluster)
    # print(DefoeService.preComputedJobID)
    print(service.get_status(job_id))

