import json
import unittest
from pathlib import Path

import engine


class EducationalEngineTests(unittest.TestCase):
    def setUp(self):
        self.story = json.loads(Path("demo/story_5min.json").read_text(encoding="utf-8"))

    def test_long_form_story_has_substantial_content(self):
        engine.validate_story(self.story)
        self.assertGreaterEqual(len(self.story["scenes"]), 15)
        words = sum(len(scene["narration"].split()) for scene in self.story["scenes"])
        self.assertGreaterEqual(words, 550)
        self.assertLessEqual(words, 900)

    def test_all_scenes_have_required_visual_fields(self):
        for scene in self.story["scenes"]:
            self.assertTrue(scene.get("visual"))
            self.assertTrue(scene.get("heading") or scene.get("caption"))
            self.assertTrue(scene.get("takeaway"))

    def test_frames_change_during_a_long_explanatory_scene(self):
        scene = {
            "heading": "Packets move across networks",
            "caption": "Routers forward packets",
            "takeaway": "Each hop moves data closer",
            "visual": "flow",
            "items": ["Device", "Router", "Provider", "Server"],
            "action": "explain",
            "duration": 30,
            "narration": "A packet moves through a series of networks.",
        }
        first = engine.make_frame(scene, 0, 720, (1280, 720), 1, 1, "Animation test")
        later = engine.make_frame(scene, 360, 720, (1280, 720), 1, 1, "Animation test")
        self.assertNotEqual(first.tobytes(), later.tobytes())

    def test_stickman_is_line_art_not_a_filled_torso(self):
        image = engine.Image.new("RGB", (640, 480), engine.BG)
        draw = engine.ImageDraw.Draw(image)
        engine.draw_character(draw, "explain", 300, 350, 1.0, 1.0)
        # The torso centreline is ink, while the adjacent body area remains empty.
        # The torso leans slightly from shoulder to hip, so sample its actual
        # interpolated centreline instead of assuming it remains at x=300.
        x = int(300 + __import__("math").sin(0.7) * 4)
        shoulder_x = x
        hip_x = x + int(__import__("math").sin(1.1) * 3)
        shoulder_y, hip_y = 350 - 99, 350 - 8
        sample_y = 290
        progress = (sample_y - shoulder_y) / (hip_y - shoulder_y)
        torso_x = round(shoulder_x + (hip_x - shoulder_x) * progress)
        self.assertNotEqual(image.getpixel((torso_x, sample_y)), engine.BG)
        self.assertEqual(image.getpixel((torso_x + 15, sample_y)), engine.BG)

    def test_caption_cues_use_word_boundary_times(self):
        boundaries = [
            {"text": "Packets", "start": 0.2, "duration": 0.3},
            {"text": "move", "start": 0.55, "duration": 0.2},
            {"text": "quickly.", "start": 0.8, "duration": 0.35},
            {"text": "across", "start": 1.3, "duration": 0.2},
            {"text": "networks.", "start": 1.55, "duration": 0.3},
        ]
        cues = engine.build_caption_cues(boundaries, "unused fallback", 3.0)
        self.assertEqual(cues[0]["text"], "Packets move quickly.")
        self.assertAlmostEqual(cues[0]["start"], 0.2)
        self.assertAlmostEqual(cues[0]["end"], 1.15)
        self.assertEqual(cues[1]["text"], "across networks.")

    def test_new_thunderstorm_script_has_full_documentary_content(self):
        story = json.loads(Path("demo/story_thunderstorm_5min.json").read_text(encoding="utf-8"))
        engine.validate_story(story)
        self.assertGreaterEqual(len(story["scenes"]), 15)
        words = sum(len(scene["narration"].split()) for scene in story["scenes"])
        self.assertGreaterEqual(words, 700)
        self.assertLessEqual(words, 1100)

    def test_solid_colour_svg_diagram_renders_and_builds_in_stages(self):
        scene = {"visual": "flow", "heading": "A coloured process", "caption": "Stages build",
                 "items": ["Warm air", "Cloud", "Rain", "Lightning"]}
        first = engine.Image.new("RGB", (1280, 720), engine.BG)
        later = engine.Image.new("RGB", (1280, 720), engine.BG)
        engine.draw_svg_diagram(first, scene, 0.2, 1280, 720, (32, 166, 138))
        engine.draw_svg_diagram(later, scene, 5.5, 1280, 720, (32, 166, 138))
        self.assertNotEqual(first.crop((460, 125, 1200, 470)).tobytes(),
                            later.crop((460, 125, 1200, 470)).tobytes())
        self.assertGreater(len(engine.SVG_CACHE), 0)

    def test_invalid_empty_story_is_rejected(self):
        with self.assertRaises(ValueError):
            engine.validate_story({"scenes": []})


if __name__ == "__main__":
    unittest.main()
