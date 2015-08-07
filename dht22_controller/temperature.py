from dht22_controller.capped_queue import CappedQueue


def c_to_f(value):
    return (value * 1.8) + 32.


class Temperature(object):

    def __init__(self, config, queue_size=10):
        self.queue = CappedQueue(cap=queue_size)
        self.cooling = False
        self.config = config

    def add(self, temperature):
        if temperature < 0. or temperature > 110.:
            return

        self.queue.put(temperature)

    def change_config(config):
        self.config = config

    def average(self):
        l = self.queue.tolist()
        return sum(l) / float(len(l))

    def update(self):
        t = self.average()
        min_temp = self.config.target_temp_fahrenheit - self.config.temp_pad
        max_temp = self.config.target_temp_fahrenheit + self.config.temp_pad
        if self.cooling:
            if t > self.config.target_temp_fahrenheit:
                return
            else:
                self.cooling = False
        elif not self.cooling:
            if t < max_temp:
                return
            else:
                self.cooling = True

    def __str__(self):
        return "temp*f={:.1f}".format(self.average())
