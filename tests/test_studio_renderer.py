import unittest
from PIL import Image

from studio_renderer import apply_style, prepare_story, transition_frame


class StudioRendererTests(unittest.TestCase):
    def test_all_visual_styles_preserve_frame_size(self):
        source = Image.new("RGB", (1280, 720), (90, 130, 170))
        for style in ("cinematic", "editorial", "neon", "paper", "playful"):
            result = apply_style(source, style)
            self.assertEqual(result.size, source.size)
            self.assertEqual(result.mode, "RGB")

    def test_invalid_visual_style_is_rejected(self):
        with self.assertRaises(ValueError):
            apply_style(Image.new("RGB", (1280, 720)), "unknown")

    def test_transition_types_have_expected_endpoints(self):
        outgoing = Image.new("RGB", (40, 30), (0, 0, 0))
        incoming = Image.new("RGB", (40, 30), (255, 255, 255))
        self.assertEqual(transition_frame(outgoing, incoming, 1, "fade"), incoming)
        self.assertEqual(transition_frame(outgoing, incoming, .5, "wipe").getpixel((39, 15)), (0, 0, 0))
        self.assertEqual(transition_frame(outgoing, incoming, 1, "zoom"), incoming)

    def test_chapters_are_added_to_scene_boundaries(self):
        story = {"scenes": [{"heading": "Hook"}, {"heading": "Detail"}, {"heading": "Payoff"}]}
        scenes = prepare_story(story, chapter_every=2)
        self.assertTrue(scenes[0]["_chapter_start"])
        self.assertFalse(scenes[1]["_chapter_start"])
        self.assertTrue(scenes[2]["_chapter_start"])
        self.assertEqual(scenes[2]["chapter"], "Payoff")


if __name__ == "__main__":
    unittest.main()
