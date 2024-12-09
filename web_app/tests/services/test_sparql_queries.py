import unittest
from web_app.query_app.controller import sparql_queries


class MyTestCase(unittest.TestCase):
    def test_get_series(self):
        collection_name = "Chapbooks printed in Scotland"
        series_list = sparql_queries.get_series(collection_name)
        print(series_list[0])
        self.assertEqual(len(series_list), 2742)

    def test_get_eb_editions(self):
        editions_list = sparql_queries.get_editions()
        print(editions_list[0])
        self.assertEqual(len(editions_list), 11)

    def test_get_series_details(self):
        series_uri = "<https://w3id.org/hto/Series/9929733583804340>"
        series_details = sparql_queries.get_series_details(series_uri)
        expect_result = {'title': "answer to Andrew Moffat's small poem, on singing church-music", 'year': '0', 'uri': '<https://w3id.org/hto/Series/9929733583804340>', 'number': '264', 'printedAt': 'Edinburgh', 'physicalDescription': '12mo.', 'MMSID': '9929733583804340', 'shelfLocator': 'L.C.2804(7)', 'genre': '0', 'language': 'English', 'numOfVolumes': '1'}
        self.assertEqual(series_details, expect_result)

    def test_get_nls_volumes(self):
        series_uri = "<https://w3id.org/hto/Series/9929733583804340>"
        volumes_list = sparql_queries.get_volumes(series_uri)
        print(volumes_list)

    def test_get_eb_volumes(self):
        edition_uri = "<https://w3id.org/hto/Edition/992277653804341>"
        volumes_list = sparql_queries.get_volumes(edition_uri)
        expect_result = [{'uri': 'https://w3id.org/hto/Volume/992277653804341_144133901', 'number': '1', 'name': 'Volume 1, A-B'}, {'uri': 'https://w3id.org/hto/Volume/992277653804341_144133902', 'number': '2', 'name': 'Volume 2, C-L'}, {'uri': 'https://w3id.org/hto/Volume/992277653804341_144133903', 'number': '3', 'name': 'Volume 3, M-Z'}]
        self.assertEqual(volumes_list, expect_result)

    def test_get_volume_details(self):
        volume_uri = "<https://w3id.org/hto/Volume/9929777383804340_193322702>"
        volume_details = sparql_queries.get_volume_details(volume_uri)
        print(volume_details)

    def test_get_volume_eb_full_details(self):
        volume_uri = "<https://w3id.org/hto/Volume/9929777383804340_193322702>"
        volume_details = sparql_queries.get_volume_full_details(volume_uri)
        print(volume_details)

    def test_get_volume_nls_full_details(self):
        volume_uri = "<https://w3id.org/hto/Volume/9929733583804340_104184378>"
        volume_details = sparql_queries.get_volume_full_details(volume_uri)
        print(volume_details)



if __name__ == '__main__':
    unittest.main()
