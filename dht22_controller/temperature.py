from dht22_controller.capped_queue import CappedQueue
from dht22_controller.utils import now, clip
from dht22_controller import learn_cool
from datetime import timedelta
import logging


logging.basicConfig(filename="/tmp/dht22_controller.log", level=logging.DEBUG)


def c_to_f(value):
    return (value * 1.8) + 32.


class Temperature(object):

    def __init__(self, config, queue_size=10, debug=False, cool_for_s=20.,
        heat_for_s=20., has_heater=False, has_cooler=False):
        self.queue = CappedQueue(cap=queue_size)
        self.config = config
        self.debug = debug
        self.cool_for_s = cool_for_s
        self.heat_for_s = heat_for_s
        self.has_heater = has_heater
        self.has_cooler = has_cooler
        self.cooling_on = False
        self.heating_on = False
        self.cooler_enabled_at = None
        self.heater_enabled_at = None
        self.last_cooling = now()
        self.last_heating = now()
        self.last_minimum = None
        self.last_maximum = None
        self.waiting_for_temp_increase = False
        self.waiting_for_temp_decrease = False
        self.start_cool_temp = None
        self.start_heat_temp = None

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

    def cooled_recently(self):
        """
        Have we cooled recently? (last 2 minutes)
        """
        return (now() - self.last_cooling) <= timedelta(minutes=2)

    def heated_recently(self):
        """
        Have we heated recently? (last 2 minutes)
        """
        return (now() - self.last_heating) <= timedelta(minutes=2)

    def temp_direction(self):
        """
        Uses the temperature queue to determine if the temperature is increasing.
        """
        l = self.queue.tolist()
        mp = len(l) / 2
        # older temperatures avg
        avg_before = sum(l[:mp]) / float(mp)
        # newer temperatures avg
        avg_after = sum(l[mp:]) / float(mp)

        if avg_before == avg_after: return 0 # unknown direction
        elif avg_before < avg_after: return 1 # increasing
        else: return -1 # decreasing

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
            if self.cooling_for() >= timedelta(seconds=self.cool_for_s):
                self.last_cooling = now()
                self.cooling_on = False
                self.waiting_for_temp_increase = True
        elif self.heating_on:
            if self.heating_for() >= timedelta(seconds=self.heat_for_s):
                self.last_heating = now()
                self.heating_on = False
                self.waiting_for_temp_decrease = True
        else:
            # --------------------------------
            # not currently heating or cooling
            # --------------------------------

            if self.waiting_for_temp_increase:
                # we just ran the cooler and are waiting for the temp to increase
                if t >= self.last_minimum + .2:
                # if self.temp_direction() == 1:
                    self.waiting_for_temp_increase = False
                    if not self.debug:
                        logging.debug('temp is now increasing. min={:.2f}'.format(self.last_minimum))

                    cool_for = self.cool_for_s
                    temp_diff = t - self.config.max_temp_f
                    if temp_diff >= .25:
                        # s_per_f should be the seconds to cool for each degree,
                        # and since we typically cool down by temp_pad * 2.,
                        # we need to divide by that amount to get the number of
                        # seconds per degree
                        s_per_f = cool_for / (self.config.temp_pad * 2.)
                        cool_for = temp_diff * s_per_f

                    if not self.debug:
                        # save what we learned from the last time
                        learn_cool.save_cool(cool_for, self.start_cool_temp, self.last_minimum)
                        self.start_cool_temp = None

                    # ----------------------------------------
                    # learn the correct amount of time to wait
                    # ----------------------------------------

                    # get the difference in temps; will be positive if we
                    # overshot
                    diff = self.config.min_temp_f - self.last_minimum

                    # multiply by 3 for a rough estimate of the amount of
                    # change in seconds
                    # examples:
                    # ---------
                    #   0.01*f -> 0.03s
                    #   0.10*f -> 0.30s
                    #   1.00*f -> 3.00s
                    diff = 3.0*diff

                    # update the number of seconds to cool for
                    self.cool_for_s = clip(cool_for - diff, 10., 60. * 5.)
            elif self.waiting_for_temp_decrease:
                # we just ran the heater and are waiting for the temp to decrease
                if t <= self.last_maximum - .2:
                # if self.temp_direction() == -1:
                    self.waiting_for_temp_decrease = False
                    if not self.debug:
                        logging.debug('temp is now decreasing. max={:.2f}'.format(self.last_maximum))

                    # TODO IMPLEMENT ME
                    # learn
                    pass
            elif t >= self.config.max_temp_f:
                if self.heated_recently(): return
                if not self.has_cooler: return
                # if it's warm and we weren't just running a heater, turn
                # our cooling on
                self.cooling_on = True
                self.cooler_enabled_at = now()
                self.last_minimum = t
                self.start_cool_temp = t
            elif t <= self.config.min_temp_f:
                if self.cooled_recently(): return
                if not self.has_heater: return
                # if it's cool and we weren't just running a cooler, turn
                # our heating on
                self.heating_on = True
                self.heater_enabled_at = now()
                self.last_maximum = t
                self.start_heat_temp = t
            else:
                pass

    def __str__(self):
        return "temp*f={:.1f}".format(self.temperature_average_f())
