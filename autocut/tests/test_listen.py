from unittest import TestCase
from autocut.listen import listen_for_start_and_end

import os 
dir_path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(dir_path,'fps25.mp4')

epsilon = 0.02

class TestParse(TestCase):
    def test_listen(self):
        starting, ending = listen_for_start_and_end(filename,before_in=0,after_out=0)
        self.assertTrue(abs(starting - 2) < epsilon)
        self.assertTrue(abs(ending - 4) < epsilon)

    def test_negative_start(self):
        starting, ending = listen_for_start_and_end(filename,before_in=10,after_out=0)
        self.assertTrue(starting == 0)

    def test_too_long(self):
        starting, ending = listen_for_start_and_end(filename,before_in=0,after_out=10)
        self.assertTrue(abs(ending - 6) < epsilon)        


