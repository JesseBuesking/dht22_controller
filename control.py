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
from dht22_controller import learn_cool
from dht22_controller.utils import clip
import logging
logging.basicConfig(filename="/tmp/dht22_controller.log", level=logging.DEBUG)

g.setmode(g.BCM)
SENSOR = Adafruit_DHT.DHT22

conf = Config()
conf.load()

temperature = Temperature(
    conf,
    queue_size=10,
    debug=False,
    cool_for_s=20.,
    heat_for_s=20.,
    has_cooler=True,
    has_heater=False,
    recently_minutes=5.)
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
def record_data(t, tavg, h, havg):
    with open('data.csv', 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow([
            # current datetime
            datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
            # current temperature
            '{:.2f}'.format(t),
            # average temperature
            '{:.2f}'.format(tavg),
            # current humidity
            '{:.2f}'.format(h),
            # average humidity
            '{:.2f}'.format(havg)])


def _get_data():
    h, t = Adafruit_DHT.read(SENSOR, conf.pin)
    if h is None or t is None:
        return (None, None)
    else:
        return (float(h), c_to_f(float(t)))


def get_data_wait():
    while True:
        h, t = _get_data()
        if h is None or t is None:
            # couldn't get a reading, so just skip
            time.sleep(1)
            continue

        # update our variables
        humidity.add(h)
        humidity.update()

        temperature.add(t)
        temperature.update()

        # record the data to csv
        record_data(t, temperature.average(), h, humidity.average())
        break

    return h, t


if __name__ == '__main__':
    # loop forever
    while True:
        h, t = get_data_wait()

        logging.debug('h={:.2f},h.avg={:.2f},humidifying={}'.format(h, humidity.average(), humidity.humidifying))
        logging.debug('t={:.2f},t.avg={:.2f},cooling={}'.format(t, temperature.average(), temperature.cooling))

        if conf.cool_pin is not None:
            g.output(conf.cool_pin, ON if temperature.cooling_on else OFF)

        # TODO enable humidity learning
        if conf.humidity_pin is not None:
            g.output(conf.humidity_pin, OFF)
            # g.output(conf.humidity_pin, ON if humidity.humidifying else OFF)

        time.sleep(1)
