import numpy as np


def cosine_similarity(word1, word2, sentence_transformer):
    vec1 = sentence_transformer.encode(word1)
    vec2 = sentence_transformer.encode(word2)
    return np.arccos((np.dot(vec1, vec2)) / ((np.linalg.norm(vec1, ord=2))*(np.linalg.norm(vec2, ord=2))))
