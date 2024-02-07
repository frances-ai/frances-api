import grpc

from web_app.defoe_service.defoe_pb2 import JobSubmitRequest, JobRequest
from web_app.defoe_service.defoe_pb2_grpc import DefoeStub


class LocalDefoeService:
    preComputedJobID = []

    @staticmethod
    def get_pre_computed_queries():
        return {
            "total_eb_hq_publication_normalized": "precomputedResult/total_eb_hq_publication_normalized.yml",
            "total_eb_publication_normalized": "precomputedResult/total_eb_publication_normalized.yml",
            "chapbooks_scotland_publication_normalized": "precomputedResult"
                                                         "/chapbooks_scotland_publication_normalized.yml",
            "gazetteers_scotland_publication_normalized": "precomputedResult"
                                                          "/gazetteers_scotland_publication_normalized.yml",
            "ladies_publication_normalized": "precomputedResult"
                                             "/ladies_publication_normalized.yml",
        }

    def __init__(self, channel):
        self.channel = channel

    def submit_job(self, job_id, model_name, query_name, endpoint, query_config, result_file_path):
        if (query_config['kg_type'] + '_' + query_name) in LocalDefoeService.get_pre_computed_queries():
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

    def get_status(self, job_id):
        if job_id in LocalDefoeService.preComputedJobID:
            LocalDefoeService.preComputedJobID.remove(job_id)
            return {
                "state": "DONE"
            }

        try:
            with grpc.insecure_channel(self.channel) as channel:
                stub = DefoeStub(channel)
                job_request = JobRequest(job_id=job_id)
                response = stub.get_job(job_request)
                if response.error and response.error != "":
                    return {
                        "state": response.state,
                        "details": response.error
                    }
                return {
                    "state": response.state
                }
        except Exception as E:
            raise Exception(E)

    def cancel_job(self, job_id):
        # TODO Implement cancel job in local defoe service
        pass


if __name__ == "__main__":
    channel = "localhost:5052"
    service = LocalDefoeService(channel)

    model_name = 'sparql'
    endpoint = 'http://www.frances-ai.com:3030/total_eb_hq/sparql'
    query_name = 'frequency_keysearch_by_year'
    query_config = {'preprocess': 'none', 'target_sentences': '', 'hit_count': 'term', 'data': '/Users/ly40/Documents/frances-ai/defoe_lib/queries/animal.txt', 'gazetteer': '', 'start_year': '1768', 'end_year': '1844', 'kg_type': 'total_eb_hq', 'window': 'None'}
    result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/publication.yml"

    #query_name = 'geoparser_by_year'
    #query_config = {'preprocess': 'none', 'target_sentences': '', 'hit_count': 'term', 'data': '/Users/ly40/Documents/frances-ai/defoe_lib/queries/scots.txt', 'gazetteer': 'geonames', 'start_year': '1770', 'end_year': '1772', 'kg_type': 'chapbooks_scotland', 'window': 'None'}
    #result_file_path = "/Users/ly40/Documents/frances-ai/frances-api/scots_geoparser.yml"
    job_id = 'cd93703f-e094-5'

    query_name = 'publication_normalized'

    service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

    # another_service = DefoeService(main_python_file_uri, python_file_uris, cluster)
    # print(DefoeService.preComputedJobID)
    print(service.get_status(job_id))

