from google.cloud import dataproc
from google.cloud.dataproc_v1 import JobStatus


def query_config_to_args(query_config):
    args = []
    for arg in query_config:
        if query_config[arg] is not None and query_config[arg] != '':
            args.append("--{}={}".format(arg, query_config[arg]))
    return args


class DefoeService:
    preComputedJobID = []

    @staticmethod
    def get_pre_computed_queries():
        return {
            "total_eb_publication_normalized": "precomputedResult/total_eb_publication_normalized.yml",
            "chapbooks_scotland_publication_normalized": "precomputedResult"
                                                         "/chapbooks_scotland_publication_normalized.yml",
            "gazetteers_scotland_publication_normalized": "precomputedResult"
                                                         "/gazetteers_scotland_publication_normalized.yml",
            "ladies_publication_normalized": "precomputedResult"
                                                         "/ladies_publication_normalized.yml",
        }

    @staticmethod
    def state_to_str(state):
        mapper = {
            JobStatus.State.DONE: "DONE",
            JobStatus.State.SETUP_DONE: "SETUP_DONE",
            JobStatus.State.ERROR: "ERROR",
            JobStatus.State.RUNNING: "RUNNING",
            JobStatus.State.PENDING: "PENDING",
            JobStatus.State.ATTEMPT_FAILURE: "ATTEMPT_FAILURE",
            JobStatus.State.CANCEL_PENDING: "CANCEL_PENDING",
            JobStatus.State.CANCEL_STARTED: "CANCEL_STARTED",
            JobStatus.State.CANCELLED: "CANCELLED",
            JobStatus.State.STATE_UNSPECIFIED: "STATE_UNSPECIFIED"
        }
        return mapper[state]

    def __init__(self, main_python_file_uri, python_file_uris, cluster):
        self.main_python_file_uri = main_python_file_uri
        self.python_file_uris = python_file_uris
        self.cluster = cluster
        self.job_client = dataproc.JobControllerClient(
            client_options={"api_endpoint": "{}-dataproc.googleapis.com:443".format(self.cluster["region"])}
        )

    def submit_job(self, job_id, model_name, query_name, endpoint, query_config, result_file_path):
        if (query_config['kg_type'] + '_' + query_name) in DefoeService.get_pre_computed_queries():
            DefoeService.preComputedJobID.append(job_id)
            return job_id

        config_args = query_config_to_args(query_config)
        args = ["--query_name={}".format(query_name), "--model_name={}".format(model_name),
                "--endpoint={}".format(endpoint), "--result_file_path={}".format(result_file_path)] + config_args

        # Create the job config.
        job = {
            "reference": {
                "job_id": job_id
            },
            "placement": {"cluster_name": self.cluster["cluster_name"]},
            "pyspark_job": {
                "main_python_file_uri": self.main_python_file_uri,
                "python_file_uris": self.python_file_uris,
                "args": args,
                "properties": {
                    "spark.executor.cores": "8",
                    "spark.executor.instances": "34",
                    "spark.dynamicAllocation.enabled": "false",
                    "spark.cores.max": "272"
                }
            },
        }

        try:
            operation = self.job_client.submit_job_as_operation(
                request={"project_id": self.cluster["project_id"], "region": self.cluster["region"], "job": job}
            )

            print("Job submitted!")
            return operation.metadata.job_id

        except Exception as E:
            raise Exception(E)

    def get_status(self, job_id):
        if job_id in DefoeService.preComputedJobID:
            DefoeService.preComputedJobID.remove(job_id)
            return {
                "state": JobStatus.State.DONE
            }

        job = self.job_client.get_job(
            request={"project_id": self.cluster["project_id"], "region": self.cluster["region"], "job_id": job_id}
        )

        if job.status.details:
            return {
                "state": job.status.state,
                "details": job.status.details
            }

        return {
            "state": job.status.state
        }

    def cancel_job(self, job_id):
        try:
            self.job_client.cancel_job(
                request={"project_id": self.cluster["project_id"], "region": self.cluster["region"], "job_id": job_id}
            )
        except Exception as e:
            raise Exception(e)


if __name__ == "__main__":
    main_python_file_uri = "gs://frances2023/run_query.py"
    python_file_uris = ["gs://frances2023/defoe.zip"]
    cluster = {
        "cluster_name": "cluster-8753",
        "project_id": "frances-365422",
        "region": "us-central1"
    }
    service = DefoeService(main_python_file_uri, python_file_uris, cluster)

    model_name = "sparql"
    query_name = "publication_normalized"
    endpoint = "http://35.228.63.82:3030/ladies/sparql"
    query_config = {
        "kg_type": "ladies",
    }
    result_file_path = "ladies_publication_normalized.yml"
    job_id = "customer_ladies_publication_normalized1"

    service.submit_job(job_id, model_name, query_name, endpoint, query_config, result_file_path)

    #another_service = DefoeService(main_python_file_uri, python_file_uris, cluster)
    #print(DefoeService.preComputedJobID)
    print(service.get_status(job_id))
