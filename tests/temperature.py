import unittest
from dht22_controller.utils import *
from dht22_controller.config import Config
from dht22_controller.temperature import Temperature
from dht22_controller.humidity import Humidity
from tests.testbase import TestBase
from datetime import datetime, timedelta
import math


c = Config()
c.config['target_temp_f'] = 60
c.config['temp_pad'] = 1


set_now(lambda: datetime(2000, 1, 1, 0, 0, 0))


optimal_time_s = 15
def temp_by_s(seconds):
    # exponential
    return float(seconds)**2. / (float(optimal_time_s)**2 / 2.)
    # # sigmoid
    # return (1. / (1. + math.exp(optimal_time_s - seconds))) * 4.


def temp_gen(last, increase=False, amount=.01):
    n = last + (amount if increase else -amount)
    # increase the time by the same amount as the temp. this way it takes
    # 1 minute to increase .1 degree, making math easier
    _now = now()
    set_now(lambda: _now + timedelta(minutes=10*amount))
    return n


class TemperatureTests(TestBase):

    def test_temp_avg(self):
        t = Temperature(c, debug=True)
        for i in range(1, 11, 1):
            t.add(i)

        self.assertEqual(5.5, t.temperature_average_f())

    def test_is_increasing_should_be_cooling(self):
        t = Temperature(c, debug=True, has_heater=True, has_cooler=True)
        last_temp = 60.
        t.add(last_temp)
        t.update()
        increasing = True

        while True:
            last_temp = temp_gen(last_temp, increasing)
            t.add(last_temp)
            t.update()
            self.assertFalse(t.heating_on)
            if increasing and t.temperature_average_f() < c.max_temp_f:
                self.assertFalse(t.cooling_on)
                increasing = True
            elif increasing and t.temperature_average_f() >= c.max_temp_f:
                self.assertTrue(t.cooling_on)
                increasing = False
            elif not increasing and (now() - t.cooler_enabled_at) >= timedelta(seconds=t.cool_for_s):
                self.assertFalse(t.cooling_on)
                break

    def test_is_decreasing_should_not_be_cooling(self):
        t = Temperature(c, debug=True, has_heater=True, has_cooler=True)
        last_temp = 60.
        t.add(last_temp)
        t.update()

        while True:
            last_temp = temp_gen(last_temp, False)
            t.add(last_temp)
            t.update()
            if t.temperature_average_f() <= c.min_temp_f:
                self.assertTrue(t.heating_on)
                self.assertFalse(t.cooling_on)
                break
            else:
                self.assertFalse(t.cooling_on)

    def test_is_decreasing_should_be_heating(self):
        t = Temperature(c, debug=True, has_heater=True, has_cooler=True)
        last_temp = 60.
        t.add(last_temp)
        t.update()
        increasing = False

        while True:
            last_temp = temp_gen(last_temp, increasing)
            t.add(last_temp)
            t.update()
            if not increasing and t.temperature_average_f() > c.min_temp_f:
                self.assertFalse(t.heating_on)
                increasing = False
            elif not increasing and t.temperature_average_f() <= c.min_temp_f:
                self.assertTrue(t.heating_on)
                increasing = True
            elif increasing and (now() - t.heater_enabled_at) >= timedelta(seconds=t.heat_for_s):
                self.assertFalse(t.heating_on)
                break

    def test_is_increasing_should_not_be_heating(self):
        t = Temperature(c, debug=True, has_heater=True, has_cooler=True)
        last_temp = 60.
        t.add(last_temp)
        t.update()

        while True:
            last_temp = temp_gen(last_temp, True)
            t.add(last_temp)
            t.update()
            if t.temperature_average_f() >= c.max_temp_f:
                self.assertTrue(t.cooling_on)
                self.assertFalse(t.heating_on)
                break
            else:
                self.assertFalse(t.heating_on)

    # ==========================================================================
    # LEARNING TESTS
    # ==========================================================================


    def test_learns_cool_for_time(self):
        t = Temperature(c, debug=True, has_cooler=True)
        last_temp = 60.
        t.add(last_temp)
        t.update()

        increasing = True

        i = e = 0
        while i < 10000:
            i += 1
            last_temp = temp_gen(last_temp, increasing)
            t.add(last_temp)
            t.update()

            if t.cooling_on:
                e += 1
                minimum = t.temperature_average_f() - temp_by_s(t.cool_for_s)
                last_temp = minimum
                if abs(minimum - c.min_temp_f) < .05:
                    print('NOTE: steady after {} learned updates'.format(e))
                    self.assertTrue(True)
                    break
                [t.add(minimum + j*.01) for j in range(t.queue.cap)]
                t.cooling_on = False
                t.waiting_for_temp_increase = True
