from dht22_controller.capped_queue import CappedQueue


class Humidity(object):

    def __init__(self, config, queue_size=10):
        self.queue = CappedQueue(cap=queue_size)
        self.humidifying = False
        self.config = config

    def add(self, humidity):
        if humidity < 0. or humidity > 100.:
            return

        self.queue.put(humidity)

    def change_config(config):
        self.config = config

    def average(self):
        l = self.queue.tolist()
        return sum(l) / float(len(l))

    def update(self):
        h = self.average()
        min_humidity = self.config.target_humidity - self.config.humidity_pad
        max_humidity = self.config.target_humidity + self.config.humidity_pad
        if self.humidifying:
            if h < self.config.target_humidity:
                return
            else:
                self.humidifying = False
        elif not self.humidifying:
            if h > min_humidity:
                return
            else:
                self.humidifying = True

    def __str__(self):
        return "humidity={:.1f}%".format(self.average())
