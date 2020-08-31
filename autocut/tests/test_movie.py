import unittest
from autocut.parse import parse_input
from autocut.melt import movie2xml

import os
dir_path = os.path.dirname(os.path.realpath(__file__))

class TestParse(unittest.TestCase):
    def test_overlay(self):
        movie = parse_input(os.path.join(dir_path,'input-overlay.xml'))
        xml = movie2xml(movie)
