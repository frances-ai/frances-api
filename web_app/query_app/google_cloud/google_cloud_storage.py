import yaml
from google.cloud import storage


class GoogleCloudStorage:
    def __init__(self, project_id, bucket_name):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.client = storage.Client(project_id)
        self.bucket = self.client.bucket(bucket_name)

    def upload_blob_from_filename(self, source_filename, destination_blob_name):
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_filename)

        print(
            f"File {source_filename} uploaded to {destination_blob_name}."
        )

    def download_blob_to_stream(self, source_blob_name, file_obj):
        blob = self.bucket.blob(source_blob_name)
        blob.download_to_file(file_obj)
        return file_obj

    def download_blob_from_filename(self, source_blob_name, destination_file_name):
        blob = self.bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)

    def read_results(self, result_filename):
        blob = self.bucket.blob(result_filename)
        with blob.open("r") as stream:
            results = yaml.safe_load(stream)
        return results



