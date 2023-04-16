import unittest

import mood


class TestMood(unittest.TestCase):
    """
    Tests the mood module
    """
    def test_getEmotions(self):
        """
        Tests the getEmotions function

        Each tests checks that the extracted emotions' scores from the transformer fall within the expected range
        """
        emotions = mood.getEmotions(["i am happy"])[0]
        for emotion in emotions:
            if emotion["label"] == "joy":
                self.assertTrue(emotion["score"] > 0.8)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["i am sad"])[0]
        for emotion in emotions:
            if emotion["label"] == "sadness":
                self.assertTrue(emotion["score"] > 0.8)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["i am angry"])[0]
        for emotion in emotions:
            if emotion["label"] == "anger":
                self.assertTrue(emotion["score"] > 0.8)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["i am scared"])[0]
        for emotion in emotions:
            if emotion["label"] == "fear":
                self.assertTrue(emotion["score"] > 0.8)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["i am disgusted"])[0]
        for emotion in emotions:
            if emotion["label"] == "disgust":
                self.assertTrue(emotion["score"] > 0.8)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["i am surprised"])[0]
        for emotion in emotions:
            if emotion["label"] == "surprise":
                self.assertTrue(emotion["score"] > 0.8)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["i am happy and sad"])[0]
        for emotion in emotions:
            if emotion["label"] == "sadness":
                self.assertTrue(emotion["score"] > 0.4)
            elif emotion["label"] == "joy":
                self.assertTrue(emotion["score"] > 0.4)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["there is a dead body on the floor"])[0]
        for emotion in emotions:
            if emotion["label"] == "sadness":
                self.assertTrue(emotion["score"] > 0.1)
            elif emotion["label"] == "disgust":
                self.assertTrue(emotion["score"] > 0.4)
            else:
                self.assertTrue(emotion["score"] < 0.15)

        emotions = mood.getEmotions(["ooh nice congrats!!!"])[0]
        for emotion in emotions:
            if emotion["label"] == "joy":
                self.assertTrue(emotion["score"] > 0.4)
            elif emotion["label"] == "surprise":
                self.assertTrue(emotion["score"] > 0.1)
            else:
                self.assertTrue(emotion["score"] < 0.15)

    def test_getMood(self):
        """
        Tests the getMood function

        Each test checks that the extracted mood from the transformer is the expected mood
        """
        self.assertEqual(mood.getMood(["i am happy"]), mood.Mood.HAPPY)
        self.assertEqual(mood.getMood(["i am sad"]), mood.Mood.SAD)
        self.assertEqual(mood.getMood(["i am angry"]), mood.Mood.ANGRY)
        self.assertEqual(mood.getMood(["i am scared"]), mood.Mood.AFRAID)
        self.assertEqual(mood.getMood(["i am disgusted"]), mood.Mood.DISGUSTED)
        self.assertEqual(mood.getMood(["i am surprised"]), mood.Mood.SURPRISED)
        self.assertEqual(mood.getMood(["there is a dead body on the floor"]), mood.Mood.DISGUSTED)
        self.assertEqual(mood.getMood(["ooh nice congrats!!!"]), mood.Mood.HAPPY)
        self.assertEqual(mood.getMood(["help!!", "the killer is behind me!!"]), mood.Mood.AFRAID)
        self.assertEqual(mood.getMood(["how did this apple get there", "i don't understand"]), mood.Mood.SURPRISED)

    def test_addCSV(self):
        """
        Tests the addCSV function

        This test checks that the assCSV function writes the data to the csv file in the correct format
        """
        with open("emotion_dataset.csv", 'w') as f:
            f.write("text,emotion\n")

        test_data = [
            ["i am happy", "happy"],
            ["i am sad", "sad"],
            ["i am angry", "angry"],
            ["i am scared", "afraid"],
            ["i am disgusted", "disgusted"],
            ["i am surprised", "surprised"],
            ["there is a dead body on the floor", "disgusted"],
            ["ooh nice congrats!!!", "happy"],
            ["help!! the killer is behind me!!", "afraid"],
            ["how did this apple get there i don't understand", "surprised"]
        ]

        with open("expected_result.csv", 'w') as f:
            f.write("text,emotion\n")
            for data in test_data:
                f.write(f"{data[0]},{data[1]}\n")

        for data in test_data:
            mood.addCSV(data[0], data[1])

        with open("emotion_dataset.csv", 'r') as test, open("expected_result.csv", 'r') as expected:
            self.assertEqual(test.read(), expected.read())


if __name__ == '__main__':
    unittest.main()
