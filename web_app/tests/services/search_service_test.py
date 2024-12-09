import unittest
from web_app.query_app.service.search_service import search


class MyTestCase(unittest.TestCase):
    def test_search_empty_keyword(self):
        # Example usage
        query = {
            'search_type': 'lexical',
            'keyword': '',
            'search_field': 'full_text',
            'exact_match': False,
            'phrase_match': False,
            'sort':"_score",
            'order': "desc",
            'from': 0,
            'size': 10,
        }
        results = search(query)
        print(results)

    def test_semantic_search(self):
        # Example usage
        query = {
            'search_type': 'semantic',
            'keyword': 'person who like sugar',
            'search_field': 'full_text',
            'exact_match': False,
            'phrase_match': False,
            'sort':"_score",
            'order': "desc",
            'from': 0,
            'size': 10,
        }
        results = search(query)
        print(results)



if __name__ == '__main__':
    unittest.main()
