import unittest
from web_app.query_app.service.search_service import search


class MyTestCase(unittest.TestCase):
    def test_search_empty_keyword(self):
        # Example usage
        query = {
            "indices": "eb",
            "keyword": "",
            "sort": [{"year_published": {"order": "asc"}}],
            "from": 0,
            "size": 5
        }
        results = search(query)
        print(results)



if __name__ == '__main__':
    unittest.main()
