import unittest
from PIL import Image
import wildlife_diagram_render as renderer

class WildlifeDiagramTests(unittest.TestCase):
    def test_each_diagram_renders_full_hd(self):
        kinds = ["habitat", "senses", "scent", "hunt", "diet", "web", "protect"]
        for kind in kinds:
            scene = {"heading": "Wildlife", "caption": "A connected ecosystem", "diagram": kind, "duration": 10}
            frame = renderer.draw_frame(scene, 12, 240, (1280, 720), 1, 7, "Forest Neighbours")
            self.assertEqual(frame.size, (1280, 720))
            self.assertEqual(frame.mode, "RGB")

    def test_diagram_animation_changes_over_time(self):
        scene = {"heading": "Following a scent", "caption": "Scent reveals hidden clues", "diagram": "scent", "duration": 12}
        first = renderer.draw_frame(scene, 0, 288, (1280, 720), 4, 7, "Forest Neighbours")
        later = renderer.draw_frame(scene, 144, 288, (1280, 720), 4, 7, "Forest Neighbours")
        self.assertNotEqual(first.tobytes(), later.tobytes())

if __name__ == "__main__":
    unittest.main()
