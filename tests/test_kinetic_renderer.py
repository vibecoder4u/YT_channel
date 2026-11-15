import unittest

from kinetic_renderer import make_kinetic_frame


class KineticRendererTests(unittest.TestCase):
    def test_renders_colorful_hd_frame(self):
        scene = {"heading": "A signal travels", "caption": "It reaches the server", "takeaway": "Each hop moves it forward", "visual": "network", "items": ["Device", "Router", "Server"], "action": "walk", "_render_duration": 8}
        frame = make_kinetic_frame(scene, 0, 192, 1, 1, "A story")
        self.assertEqual(frame.size, (1280, 720))
        self.assertEqual(frame.mode, "RGB")

    def test_animation_changes_over_time(self):
        scene = {"heading": "A signal travels", "caption": "It reaches the server", "takeaway": "Each hop moves it forward", "visual": "flow", "items": ["Device", "Router", "Server"], "action": "walk", "_render_duration": 8}
        first = make_kinetic_frame(scene, 0, 192, 1, 1, "A story")
        later = make_kinetic_frame(scene, 96, 192, 1, 1, "A story")
        self.assertNotEqual(first.tobytes(), later.tobytes())

    def test_scene_number_changes_color_treatment(self):
        scene = {"heading": "A new chapter", "caption": "New scene", "items": ["Idea"]}
        first = make_kinetic_frame(scene, 20, 100, 1, 3, "A story")
        later = make_kinetic_frame(scene, 20, 100, 2, 3, "A story")
        self.assertNotEqual(first.tobytes(), later.tobytes())


if __name__ == "__main__":
    unittest.main()
