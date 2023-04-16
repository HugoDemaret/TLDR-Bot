import unittest

import torch
from sentence_transformers import SentenceTransformer

from tldr import embedding, distance

sentenceModel = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')


class TestTldr(unittest.TestCase):
    def test_embedding(self):
        emb = embedding("Hello world")
        self.assertEqual(emb.shape, torch.Size([384]))
        self.assertEqual(emb.dtype, torch.float32)
        print(emb)

    def test_similarity(self):
        emb1 = embedding("Blue")
        emb2 = embedding("Blue")
        emb3 = embedding("Red")
        emb4 = embedding("Blue Blue")
        emb5 = embedding("Blue Red")
        self.assertEqual(distance(emb1, emb2), 0)
        self.assertTrue(0 < distance(emb1, emb3) < 0.3)
        d = distance(emb1, emb4)
        self.assertTrue(0 < d < 0.3)
        d = distance(emb1, emb5)
        print(d)
        self.assertTrue(0 < d < 0.3)
        emb6 = embedding("car")
        emb7 = embedding("growth")
        d = distance(emb6, emb7)
        print(d)


if __name__ == '__main__':
    unittest.main()
