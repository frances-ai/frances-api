import unittest
from google_cloud_storage import GoogleCloudStorage


class MyTestCase(unittest.TestCase):

    def setUp(self):
        PROJECT_ID = "frances-365422"
        BUCKET_NAME = "frances2023"
        self.gs = GoogleCloudStorage(PROJECT_ID, BUCKET_NAME)

    def test_read_large_file(self):
        filename = "defoe_results/d89eb31e-31f6-537f-bbe4-6d6be4b99426/160eebe5-7751-524d-9b85-f598bc4f76cd.yml"
        results = self.gs.read_results(filename)
        print(len(results))


if __name__ == '__main__':
    unittest.main()
