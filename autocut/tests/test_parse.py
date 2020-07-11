from unittest import TestCase
from autocut.parse import parse_input

import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

class TestParse(TestCase):
    def test_parse(self):
        movie = parse_input(os.path.join(dir_path,'input.xml'))
        self.assertTrue(movie['author'] == 'Sample Person')
        self.assertTrue(movie['title'] == 'Sample Title')
        self.assertTrue(len(movie['videos']) == 2)
        self.assertTrue(movie['videos'][0]['src'] == 'title.mp4')
        
