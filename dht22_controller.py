#!/usr/bin/python
from dht22_controller._logging import setup_logging
setup_logging(default_path="/home/pi/dht22_controller/logging.json")


import csv
from datetime import datetime
import sys
import time
import Adafruit_DHT
import RPi.GPIO as g
from dht22_controller.config import Config
from dht22_controller.temperature import Temperature, c_to_f
from dht22_controller.humidity import Humidity
from dht22_controller.utils import clip


import logging
log = logging.getLogger(__name__)


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
humidity = Humidity(
    conf,
    queue_size=10,
    debug=False,
    has_humidifier=False,
    has_dehumidifier=True,
    recently_minutes=5.)


# Reversed since that's what's working for me (must have reversed polarity
# on current socket?)
ON = False
OFF = True


# #### SETUP PINS ####
if conf.cool_pin is not None:
    g.setup(conf.cool_pin, g.OUT)

if conf.dehumidity_pin is not None:
    g.setup(conf.dehumidity_pin, g.OUT)


#### HELPER FUNCTIONS ####
def record_data(t, tavg, h, havg):
    with open('/home/pi/controller_data/data.csv', 'a') as csvfile:
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
        record_data(t, temperature.temperature_average_f(), h, humidity.average())
        break

    return h, t


if __name__ == '__main__':
    try:
        log.info(80*"=")
        log.info("starting dht22_controller")
        log.info(80*"=")
        log.info("")
        
        # loop forever
        while True:
            h, t = get_data_wait()

            log.debug(
                'h=%.02f (avg=%.02f) dehumid=%s | t=%.02f (avg=%.02f) cool=%s',
                h, humidity.average(),
                'on' if humidity.dehumidifier_on else 'off',
                t, temperature.temperature_average_f(),
                'on' if temperature.cooling_on else 'off',
                )

            if conf.cool_pin is not None:
                g.output(conf.cool_pin, ON if temperature.cooling_on else OFF)

            if conf.dehumidity_pin is not None:
                g.output(conf.dehumidity_pin, ON if humidity.dehumidifier_on else OFF)

            time.sleep(1)
    except Exception as e:
        log.exception("an exception occurred in the main loop")
        raise
