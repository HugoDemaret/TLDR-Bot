import socialGraph
import unittest

class testSocialGraph(unittest.TestCase):
    def test_importance_empty(self):
        socialgraph = socialGraph.SocialGraph(1,0,0.51,dict(),dict(),dict())

    def test_importance(self):
        socialgraph = socialGraph.SocialGraph()

    def test_agreement(self):
        print("l")