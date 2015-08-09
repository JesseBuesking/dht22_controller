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
from dht22_controller import learn_cool, util
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


cool_seconds = util.clip(
    learn_cool.load_last_cool(default_seconds=30.),
    # at least 10 seconds
    10.,
    # at most 5 minutes
    60. * 5.)


#### HELPER FUNCTIONS ####
def record_data(t, tavg, h, havg):
    # RECORD THE TEMPERATURE
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


def wait_until_increasing(increase_at_least=.2):
    min_temp = 200.
    while True:
        h, t = get_data_wait()

        min_temp = min(temperature.average(), min_temp)
        if (temperature.average() - min_temp) > increase_at_least:
            return min_temp

        time.sleep(1)


if __name__ == '__main__':
    # loop forever
    while True:
        h, t = get_data_wait()

        logging.debug('h={:.2f},h.avg={:.2f},humidifying={}'.format(h, humidity.average(), humidity.humidifying))
        logging.debug('t={:.2f},t.avg={:.2f},cooling={}'.format(t, temperature.average(), temperature.cooling))

        if conf.cool_pin is not None:
            if temperature.cooling:
                # we need to cool, so turn on the cooler on wait for a bit
                cool_for = cool_seconds
                max_temp = conf.target_temp_fahrenheit + conf.temp_pad
                temp_diff = temperature.average() - max_temp
                learn = True
                if temp_diff > .2:
                    # we're really warm, so the cooler might be turning on
                    # for the first time, the power went out, etc. So we need
                    # to run for longer.
                    learn = False
                    # cool_for should be the seconds to cool for each degree,
                    # and since we typically cool down by conf.temp_pad * 2.,
                    # we need to divide by that amount to get the number of
                    # seconds per degree
                    cool_for = cool_seconds / (conf.temp_pad * 2.)
                    # use an 90% multiplier so it doesn't overcool
                    cool_for = temp_diff * cool_for * .9

                logging.debug('cool_seconds={:.1f},cool_for={:.1f},max_temp={:.2f}'.format(cool_seconds, cool_for, max_temp))
                g.output(conf.cool_pin, ON)
                while cool_for > 0:
                    time.sleep(1 if cool_for > 1 else cool_for)
                    h, t = get_data_wait()
                    cool_for -= 1

                # stop cooling
                g.output(conf.cool_pin, OFF)
                temperature.cooling = False

                # wait until the temperature settles and starts increasing
                min_temp = wait_until_increasing()
                logging.debug('temp is now increasing. min={:.2f}'.format(min_temp))

                if learn:
                    # save what we learned
                    learn_cool.save_cool(cool_seconds, min_temp)

                    # learn the correct amount of time to wait
                    # ----------------------------------------------------------
                    # get the difference in temps; will be positive if we
                    # overshot
                    diff = (conf.target_temp_fahrenheit - conf.temp_pad) - min_temp
                    # multiply by 10 for a rough estimate of the amount of
                    # change in seconds
                    #   .01*f -> .03s
                    #   .1*f  -> .3s
                    #   1*f   -> 3s
                    diff *= 3.
                    # update the number of seconds to cool for
                    cool_seconds = cool_seconds - diff
                    cool_seconds = util.clip(cool_seconds, 10., 60. * 5.)
            else:
                g.output(conf.cool_pin, OFF)

        # TODO enable humidity learning
        if conf.humidity_pin is not None:
            g.output(conf.humidity_pin, OFF)
            # g.output(conf.humidity_pin, ON if humidity.humidifying else OFF)

        time.sleep(1)
