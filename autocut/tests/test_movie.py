import unittest
from autocut.parse import parse_input
from autocut.melt import movie2xml, read_image_size

import os
dir_path = os.path.dirname(os.path.realpath(__file__))

class TestParse(unittest.TestCase):
    def test_overlay(self):
        movie = parse_input(os.path.join(dir_path,'input-overlay.xml'))
        xml = movie2xml(movie)

    def test_image_size(self):
        (width,height) = read_image_size (os.path.join(dir_path,'slide.png'))
        assert (width,height) == (1920, 1080)
