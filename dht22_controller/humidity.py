from dht22_controller.capped_queue import CappedQueue
from dht22_controller.utils import now, clip
from datetime import timedelta


import logging
log = logging.getLogger(__name__)


class Humidity(object):

    def __init__(self, config, queue_size=10, debug=False, has_humidifier=False,
        has_dehumidifier=False, recently_minutes=5.):
        self.queue = CappedQueue(cap=queue_size)
        self.config = config
        self.humidifier_on = False
        self.dehumidifier_on = False
        self.has_humidifier = has_humidifier
        self.has_dehumidifier = has_dehumidifier
        self.recently_minutes = recently_minutes
        self.humidifier_enabled_at = None
        self.dehumidifier_enabled_at = None
        self.start_humidifier_value = None
        self.start_dehumidifier_value = None
        self.last_humidified = now() - timedelta(minutes=recently_minutes)
        self.last_dehumidified = now() - timedelta(minutes=recently_minutes)
        self.last_minimum = None
        self.last_maximum = None
        self.debug = debug

    def add(self, humidity):
        if humidity < 0. or humidity > 100.:
            return

        self.queue.put(humidity)

    def change_config(config):
        self.config = config

    def average(self):
        l = self.queue.tolist()
        return sum(l) / float(len(l))

    def humidified_recently(self):
        """
        Have we humidified recently?
        """
        return (now() - self.last_humidified) <= timedelta(
            minutes=self.recently_minutes)

    def dehumidified_recently(self):
        """
        Have we dehumidified recently?
        """
        return (now() - self.last_dehumidified) <= timedelta(minutes=
            self.recently_minutes)

    def update(self):
        h = self.average()
        if self.last_maximum is None: self.last_maximum = h
        if self.last_minimum is None: self.last_minimum = h
        self.last_maximum = max(h, self.last_maximum)
        self.last_minimum = min(h, self.last_minimum)

        log.debug('h=%.02f max=%.02f', h, self.config.max_humidity)
        if self.humidifier_on:
            if h < self.config.max_humidity:
                return
            self.last_humidified = now()
            self.humidifier_on = False
        elif self.dehumidifier_on:
            if h > self.config.min_humidity:
                return
            self.last_dehumidified = now()
            self.dehumidifier_on = False
        elif h <= self.config.min_humidity:
            if self.dehumidified_recently(): return
            if not self.has_humidifier: return
            # if it's dry and we weren't just running the dehumidifier, turn
            # our humidifier on
            self.humidifier_on = True
            self.humidifier_enabled_at = now()
            self.last_maximum = h
            self.start_humidifier_value = h
        elif h >= self.config.max_humidity:
            if self.humidified_recently(): return
            if not self.has_dehumidifier: return
            # if it's humid and we weren't just running the humidifier, turn
            # our dehumidifier on
            self.dehumidifier_on = True
            self.dehumidifier_enabled_at = now()
            self.last_minimum = h
            self.start_dehumidifier_value = h
        else:
            pass

    def __str__(self):
        return "humidity={:.1f}%".format(self.average())
