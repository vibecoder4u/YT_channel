import unittest

from script_to_story import script_to_story, split_into_scenes


class ScriptToStoryTests(unittest.TestCase):
    def test_blank_lines_are_scene_breaks_and_sentences_group(self):
        script = "First sentence. Second sentence. Third sentence. Fourth sentence.\n\nAnother scene."
        self.assertEqual(split_into_scenes(script), [
            "First sentence. Second sentence. Third sentence.",
            "Fourth sentence.",
            "Another scene.",
        ])

    def test_plain_script_generates_renderer_compatible_scenes(self):
        story = script_to_story("First, the signal reaches a router. Then, it travels to the server.")
        self.assertEqual(story["title"], "A Story, Illustrated")
        self.assertEqual(len(story["scenes"]), 1)
        scene = story["scenes"][0]
        for field in ("heading", "caption", "narration", "visual", "items", "action", "accent"):
            self.assertIn(field, scene)
        self.assertEqual(scene["visual"], "network")

    def test_compare_scene_gets_two_comparison_labels(self):
        story = script_to_story("Before, the process was slow. After, it became faster.")
        self.assertEqual(story["scenes"][0]["visual"], "compare")
        self.assertEqual(story["scenes"][0]["items"], ["Before", "After"])

    def test_empty_script_is_rejected(self):
        with self.assertRaises(ValueError):
            script_to_story(" \n  ")


if __name__ == "__main__":
    unittest.main()
