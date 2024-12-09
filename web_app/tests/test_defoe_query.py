def test_download(client):
    result_filename = '7c1d311f-e1ba-57db-beaf-b854fdc5c348.yml'
    response = client.post("/protected/query/download", json={'result_filename': result_filename})
    print(response)