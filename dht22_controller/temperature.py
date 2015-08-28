from dht22_controller.capped_queue import CappedQueue
from dht22_controller.utils import now, clip
from dht22_controller.learn import *
from dht22_controller.datastore import load, save
from datetime import timedelta
import logging


logging.basicConfig(filename="/tmp/dht22_controller.log", level=logging.DEBUG)


def c_to_f(value):
    return (value * 1.8) + 32.


class Temperature(object):

    def __init__(self, config, queue_size=10, debug=False, cool_for_s=20.,
        heat_for_s=20., has_cooler=False, has_heater=False, recently_minutes=5.):
        self.queue = CappedQueue(cap=queue_size)
        self.config = config
        self.debug = debug
        self.learn_cool_file = "/home/pi/controller_data/lcool.csv"
        self.learn_heat_file = "/home/pi/controller_data/lheat.csv"
        self.cool_for_s = self.load_cool(cool_for_s)
        self.heat_for_s = self.load_heat(heat_for_s)
        self.has_heater = has_heater
        self.has_cooler = has_cooler
        self.cooling_on = False
        self.heating_on = False
        self.cooler_enabled_at = None
        self.heater_enabled_at = None
        self.last_cooling = now() - timedelta(minutes=recently_minutes)
        self.last_heating = now() - timedelta(minutes=recently_minutes)
        self.last_minimum = None
        self.last_maximum = None
        self.waiting_for_temp_increase = False
        self.waiting_for_temp_decrease = False
        self.start_cool_temp = None
        self.start_heat_temp = None
        self.recently_minutes = recently_minutes

    def load_cool(self, default_seconds=45.):
        return load(self.learn_cool_file, default_seconds,
            self.config.min_temp_f)

    def save_cool(self, seconds, starting_temp, resulting_temp):
        save(self.learn_cool_file, starting_temp, self.config.min_temp_f,
            resulting_temp, seconds)

    def load_heat(self, default_seconds=45.):
        return load(self.learn_heat_file, default_seconds,
            self.config.max_temp_f)

    def save_heat(self, seconds, starting_temp, resulting_temp):
        save(self.learn_heat_file, starting_temp, self.config.max_temp_f,
            resulting_temp, seconds)

    def add(self, temperature):
        """
        Add a temperature to the queue.
        """
        if temperature < 0. or temperature > 110.: return
        self.queue.put(temperature)

    def change_config(config):
        """
        Update the config.
        """
        self.config = config

    def temperature_average_f(self):
        """
        Get the average temperature from the queue.
        """
        l = self.queue.tolist()
        return sum(l) / float(len(l))

    def cooling_for(self):
        """
        How long we've been cooling for.
        """
        if self.cooler_enabled_at is None: return None
        return now() - self.cooler_enabled_at

    def heating_for(self):
        """
        How long we've been heating for.
        """
        if self.heater_enabled_at is None: return None
        return now() - self.heater_enabled_at

    def cooled_recently(self, minutes=None):
        """
        Have we cooled recently?
        """
        minutes = self.recently_minutes if minutes is None else minutes
        return (now() - self.last_cooling) <= timedelta(minutes=minutes)

    def heated_recently(self, minutes=None):
        """
        Have we heated recently?
        """
        minutes = self.recently_minutes if minutes is None else minutes
        return (now() - self.last_heating) <= timedelta(minutes=minutes)

    def update(self):
        """
        Update our flags. This enables / disables heating and cooling given
        our queue of temperatures.
        """
        t = self.temperature_average_f()
        if self.last_maximum is None: self.last_maximum = t
        if self.last_minimum is None: self.last_minimum = t
        self.last_maximum = max(t, self.last_maximum)
        self.last_minimum = min(t, self.last_minimum)

        if self.cooling_on:
            secs_reached = self.cooling_for() >= timedelta(seconds=self.cool_for_s)
            overshooting = t < self.config.min_temp_f # overshooting the temp
            if secs_reached or overshooting:
                self.last_cooling = now()
                self.cooling_on = False
                self.waiting_for_temp_increase = True
                # we're overshooting the temp, so set the time to cool for
                # equal to the current elapsed time
                if overshooting: self.cool_for_s = self.cooling_for()
        elif self.heating_on:
            secs_reached = self.heating_for() >= timedelta(seconds=self.heat_for_s)
            overshooting = t > self.config.max_temp_f # overshooting the temp
            if secs_reached or overshooting:
                self.last_heating = now()
                self.heating_on = False
                self.waiting_for_temp_decrease = True
                # we're overshooting the temp, so set the time to cool for
                # equal to the current elapsed time
                if overshooting: self.cool_for_s = self.heating_for()
        else:
            # --------------------------------
            # not currently heating or cooling
            # --------------------------------

            if self.waiting_for_temp_increase:
                # we just ran the cooler and are waiting for the temp to increase
                if self.cooled_recently(1.): return
                if t < self.last_minimum + .2:
                    return

                self.waiting_for_temp_increase = False
                if not self.debug:
                    logging.debug('temp is now increasing. min={:.2f}'.format(self.last_minimum))

                cool_for, diff = learn(
                    save=self.save_cool,
                    current_time_s=self.cool_for_s,
                    starting_value=self.start_cool_temp,
                    starting_threshold=self.config.max_temp_f,
                    pad=self.config.temp_pad,
                    target=self.config.min_temp_f,
                    actual=self.last_minimum,
                    debug=self.debug,
                    multiplier=3.0,
                    increasing=False)
                if not self.debug:
                    logging.debug(
                        'last_s={:.1f},run_s={:.1f},target={:.2f},actual={:.2f}'.format(
                            self.cool_for_s, cool_for, self.config.min_temp_f,
                            self.last_minimum))

                # update the number of seconds to cool for
                min_cool_time_s = 10.
                max_cool_time_s = 60. * 5.
                self.cool_for_s = clip(
                    cool_for - diff, min_cool_time_s, max_cool_time_s)
            elif self.waiting_for_temp_decrease:
                # we just ran the heater and are waiting for the temp to decrease
                if self.heated_recently(1.): return
                if t > self.last_maximum - .2:
                    return

                self.waiting_for_temp_decrease = False
                if not self.debug:
                    logging.debug('temp is now decreasing. max={:.2f}'.format(self.last_maximum))

                heat_for, diff = learn(
                    save=self.save_heat,
                    current_time_s=self.heat_for_s,
                    starting_value=self.start_heat_temp,
                    starting_threshold=self.config.min_temp_f,
                    pad=self.config.temp_pad,
                    target=self.config.max_temp_f,
                    actual=self.last_maximum,
                    debug=self.debug,
                    multiplier=3.0,
                    increasing=True)
                if not self.debug:
                    logging.debug(
                        'last_s={:.1f},run_s={:.1f},target={:.2f},actual={:.2f}'.format(
                            self.heat_for_s, heat_for, self.config.max_temp_f,
                            self.last_maximum))

                # update the number of seconds to heat for
                min_heat_time_s = 3.
                max_heat_time_s = 60. * 5.
                self.heat_for_s = clip(
                    heat_for + diff, min_heat_time_s, max_heat_time_s)
            elif t >= self.config.max_temp_f:
                if self.heated_recently(): return
                if self.cooled_recently(2.5): return
                if not self.has_cooler: return
                # if it's warm and we weren't just running a heater, turn
                # our cooling on
                self.cooling_on = True
                self.cooler_enabled_at = now()
                self.last_minimum = t
                self.start_cool_temp = t

                min_cool_time_s = 10.
                max_cool_time_s = 60. * 5.
                self.cool_for_s = clip(
                    time_boost(
                        self.cool_for_s, t, self.config.max_temp_f, self.config.temp_pad, increasing=False),
                    min_cool_time_s,
                    max_cool_time_s)
                if not self.debug:
                    logging.debug('cooling for {:.2f}s'.format(self.cool_for_s))
            elif t <= self.config.min_temp_f:
                if self.heated_recently(2.5): return
                if self.cooled_recently(): return
                if not self.has_heater: return
                # if it's cool and we weren't just running a cooler, turn
                # our heating on
                self.heating_on = True
                self.heater_enabled_at = now()
                self.last_maximum = t
                self.start_heat_temp = t

                min_heat_time_s = 3.
                max_heat_time_s = 60. * 5.
                self.heat_for_s = clip(
                    time_boost(
                        self.heat_for_s, t, self.config.min_temp_f, self.config.temp_pad, increasing=True),
                    min_heat_time_s,
                    max_heat_time_s)
                if not self.debug:
                    logging.debug('heating for {:.2f}s'.format(self.heat_for_s))
            else:
                pass

    def __str__(self):
        return "temp*f={:.1f}".format(self.temperature_average_f())
