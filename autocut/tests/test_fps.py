from unittest import TestCase
from autocut.melt import read_fps
import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

class TestFps(TestCase):
    def test_fps_of_movie(self):
        fps = read_fps(os.path.join(dir_path,'fps25.mp4'))
        self.assertTrue(25 == fps)
        
        
        
