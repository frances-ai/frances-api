import unittest
from web_app.query_app.service.nlp_service import get_sentence_embedding


class NlpServiceTest(unittest.TestCase):
    def test_getting_embedding(self):
        test_sentence = "Person who like sugar!"
        print("" + get_sentence_embedding(test_sentence))

