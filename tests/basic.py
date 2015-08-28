import unittest
from dht22_controller.config import Config
from tests.testbase import TestBase


CONF = Config()


class BasicTests(TestBase):

    def test_nothing(self):
        pass

    # # DEPENDS ON CONFIG
    # def test_loads_config(self):
    #     c = Config()
    #     c.load()
    #
    #     self.assertEqual(c.pin, 5)
    #     self.assertEqual(c.target_temp_f, 60)
    #     self.assertEqual(c.temp_pad, 2)
    #     self.assertEqual(c.target_humidity, 70)
    #     self.assertEqual(c.humidity_pad, 2)
    #     self.assertEqual(c.cool_pin, 17)
    #     self.assertEqual(c.humidity_pin, 16)
