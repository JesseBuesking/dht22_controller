#!/usr/bin/python

import csv
from datetime import datetime
import sys
import time
import Adafruit_DHT
import RPi.GPIO as g
from dht22_controller.config import Config
from dht22_controller.temperature import Temperature, c_to_f
from dht22_controller.humidity import Humidity
import logging
logging.basicConfig(filename="/tmp/dht22_controller.log", level=logging.DEBUG)

g.setmode(g.BCM)
SENSOR = Adafruit_DHT.DHT22

conf = Config()
conf.load()
temperature = Temperature(conf)
humidity = Humidity(conf)


# Reversed since that's what's working for me (must have reversed polarity
# on current socket?)
ON = False
OFF = True


# #### SETUP PINS ####
if conf.cool_pin is not None:
    g.setup(conf.cool_pin, g.OUT)

if conf.humidity_pin is not None:
    g.setup(conf.humidity_pin, g.OUT)


#### HELPER FUNCTIONS ####
def get_data():
    h, t = Adafruit_DHT.read(SENSOR, conf.pin)
    if h is None or t is None:
        return (None, None)
    else:
        return (float(h), c_to_f(float(t)))


if __name__ == '__main__':
    # loop forever
    while True:
        h, t = get_data()
        if h is None or t is None:
            # couldn't get a reading, so just skip
            time.sleep(1)
            continue

        humidity.add(h)
        humidity.update()

        temperature.add(t)
        temperature.update()

        logging.debug('h={:.2f},t={:.2f}'.format(h, t))
        logging.debug('t.avg={},h.avg={}'.format(temperature.average(), humidity.average()))
        logging.debug('t.cooling={},h.humidifying={}'.format(temperature.cooling, humidity.humidifying))

        if conf.cool_pin is not None:
            g.output(conf.cool_pin, ON if temperature.cooling else OFF)

        if conf.humidity_pin is not None:
            g.output(conf.humidity_pin, ON if humidity.humidifying else OFF)

        # RECORD THE TEMPERATURE
        with open('data.csv', 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow([
                # current datetime
                datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
                # current temperature
                '{:.2f}'.format(t),
                # average temperature
                '{:.2f}'.format(temperature.average()),
                # current humidity
                '{:.2f}'.format(h),
                # average humidity
                '{:.2f}'.format(humidity.average())])

        time.sleep(1)
