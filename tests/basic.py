import unittest
from dht22_controller.config import Config
from dht22_controller.temperature import Temperature
from dht22_controller.humidity import Humidity
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

    def test_humidity_avg(self):
        h = Humidity(CONF)
        for i in range(1, 11, 1):
            h.add(i)

        self.assertEqual(5.5, h.average())

    def test_turn_humidity_on(self):
        t = Humidity(CONF, queue_size=1)

        # valid range
        t.add(70)
        t.update()
        self.assertFalse(t.humidifying)

        # valid range
        t.add(69)
        t.update()
        self.assertFalse(t.humidifying)

        # at the min allowed humidity, so we should turn on
        t.add(68)
        t.update()
        self.assertTrue(t.humidifying)

        # still humidifying
        t.add(70)
        t.update()
        self.assertTrue(t.humidifying)

        # done humidifying since we're at the max allowed humidity
        t.add(72)
        t.update()
        self.assertFalse(t.humidifying)

        # valid range
        t.add(72)
        t.update()
        self.assertFalse(t.humidifying)
