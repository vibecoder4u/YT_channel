import unittest
from PIL import ImageChops

import animal_render


class AnimalRendererTests(unittest.TestCase):
    def test_forest_scene_renders_full_hd_frame(self):
        scene = {
            "heading": "Meet the red fox",
            "caption": "A fox listens to the forest",
            "environment_label": "WOODLAND",
            "animal_action": "look",
            "movement": "hold",
            "duration": 12,
        }
        frame = animal_render.draw_scene(scene, 0, 288, (1280, 720), 1, 7, "Forest Neighbours")
        self.assertEqual(frame.size, (1280, 720))
        self.assertEqual(frame.mode, "RGB")

    def test_fox_animation_changes_between_frames(self):
        scene = {
            "heading": "Following a scent",
            "caption": "The fox investigates the forest floor",
            "environment_label": "SCENT TRAILS",
            "animal_action": "sniff",
            "movement": "hold",
            "duration": 12,
        }
        first = animal_render.draw_scene(scene, 0, 288, (1280, 720), 1, 7, "Forest Neighbours")
        later = animal_render.draw_scene(scene, 96, 288, (1280, 720), 1, 7, "Forest Neighbours")
        self.assertNotEqual(first.tobytes(), later.tobytes())


if __name__ == "__main__":
    unittest.main()
