import unittest

from script_to_story import generate_explainer_story, script_to_story


class StudioStoryTests(unittest.TestCase):
    def test_script_scenes_receive_chapter_labels(self):
        story = script_to_story("First. Second. Third. Fourth. Fifth.", max_sentences=1)
        self.assertEqual(len(story["scenes"]), 5)
        self.assertEqual(story["scenes"][0]["chapter"], "Chapter 1")
        self.assertEqual(story["scenes"][2]["chapter"], "Chapter 2")

    def test_topic_mode_generates_research_outline_not_fabricated_facts(self):
        story = generate_explainer_story("How do solar panels work?")
        self.assertEqual(len(story["scenes"]), 6)
        narration = " ".join(scene["narration"] for scene in story["scenes"])
        # The outline advises checking the source, without inventing a statistic.
        self.assertIn("trustworthy statistic", narration)
        self.assertIn("checking its source", narration)
        self.assertEqual(story["scenes"][2]["visual"], "flow")
        self.assertEqual(story["scenes"][3]["visual"], "compare")

    def test_empty_topic_fails_clearly(self):
        with self.assertRaises(ValueError):
            generate_explainer_story("   ")


if __name__ == "__main__":
    unittest.main()
