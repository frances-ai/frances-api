from sentence_transformers import SentenceTransformer

model = None


def get_model():
    global model
    if model is not None:
        return model
    model = SentenceTransformer('all-mpnet-base-v2')
    model._first_module().max_seq_length = 509
    return model


def get_sentence_embedding(sentence):
    return get_model().encode(sentence)
