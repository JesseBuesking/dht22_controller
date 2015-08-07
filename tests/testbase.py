import sys
from termcolor import colored
import unittest
from wwtw import StopWatch


class TestBase(unittest.TestCase):

    def setUp(self):
        self.sw = StopWatch()
        self.sw.start()

    def tearDown(self):
        self.sw.stop()
        sys.stdout.write('[PERF {}] '.format(colored(self.sw.pretty(6), 'blue')))
        sys.stdout.flush()
