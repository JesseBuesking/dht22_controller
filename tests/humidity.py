import unittest
from dht22_controller import *
from tests.testbase import TestBase
from datetime import datetime, timedelta
import math


c = Config()
c.config['target_humidity'] = 62
c.config['humidity_pad'] = 2


set_now(lambda: datetime(2000, 1, 1, 0, 0, 0))


def humidity_gen(last, increase=False, amount=.01):
    n = last + (amount if increase else -amount)
    # increase the time by the same amount as the temp. this way it takes
    # 1 minute to increase .1 degree, making math easier
    _now = now()
    set_now(lambda: _now + timedelta(minutes=10*amount))
    return n


class HumidityTests(TestBase):

    def test_humidity_avg(self):
        h = Humidity(c, debug=True)
        for i in range(1, 11, 1):
            h.add(i)

        self.assertEqual(5.5, h.average())

    def test_is_increasing_should_be_dehumidifying(self):
        h = Humidity(c, debug=True, has_dehumidifier=True)

        last_humid = 62.
        h.add(last_humid)
        h.update()
        increasing = True
        while True:
            last_humid = humidity_gen(last_humid, increasing)
            h.add(last_humid)
            h.update()
            self.assertFalse(h.humidifier_on)
            if increasing and h.average() < c.max_humidity:
                self.assertFalse(h.dehumidifier_on)
                increasing = True
            elif increasing and h.average() >= c.max_humidity:
                self.assertTrue(h.dehumidifier_on)
                increasing = False
            elif not increasing and (h.average() > c.min_humidity):
                self.assertTrue(h.dehumidifier_on)
                increasing = False
            elif not increasing and (h.average() <= c.min_humidity):
                self.assertFalse(h.dehumidifier_on)
                break

    def test_is_decreasing_should_not_be_dehumidifying(self):
        h = Humidity(c, debug=True, has_dehumidifier=True)

        last_humid = 62.
        h.add(last_humid)
        h.update()

        while True:
            last_humid = humidity_gen(last_humid, False)
            h.add(last_humid)
            h.update()

            if h.average() <= c.min_humidity:
                self.assertFalse(h.dehumidifier_on)
                break
            else:
                self.assertFalse(h.dehumidifier_on)

    def test_is_decreasing_should_be_humidifying(self):
        h = Humidity(c, debug=True, has_humidifier=True)

        last_humid = 62.
        h.add(last_humid)
        h.update()
        increasing = False

        while True:
            last_humid = humidity_gen(last_humid, increasing)
            h.add(last_humid)
            h.update()
            if not increasing and h.average() > c.min_humidity:
                self.assertFalse(h.humidifier_on)
                increasing = False
            elif not increasing and h.average() <= c.min_humidity:
                self.assertTrue(h.humidifier_on)
                increasing = True
            elif increasing and (h.average() < c.max_humidity):
                self.assertTrue(h.humidifier_on)
                increasing = True
            elif increasing and (h.average() >= c.max_humidity):
                self.assertFalse(h.humidifier_on)
                break

    def test_is_increasing_should_not_be_humidifying(self):
        h = Humidity(c, debug=True, has_dehumidifier=True)

        last_humid = 62.
        h.add(last_humid)
        h.update()

        while True:
            last_humid = humidity_gen(last_humid, True)
            h.add(last_humid)
            h.update()

            if h.average() >= c.max_humidity:
                self.assertFalse(h.humidifier_on)
                break
            else:
                self.assertFalse(h.humidifier_on)
