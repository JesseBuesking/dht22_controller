import json
from os.path import dirname, join
import os

CURRENTOS = 'linux'
ISWINDOWS = False
ISLINUX = False

if os.name == 'posix':
    CURRENTOS = 'linux'
    ISLINUX = True
elif os.name == 'nt':
    CURRENTOS = 'windows'
    ISWINDOWS = True

class Config(object):

    def __init__(
        self,
        default_pin=5,
        default_target_temp_f=60,
        default_temp_pad=2,
        default_target_humidity=70,
        default_humidity_pad=2):
        self.config = {}
        self.default_pin = default_pin
        self.default_target_temp_f = default_target_temp_f
        self.default_temp_pad = default_temp_pad
        self.default_target_humidity = default_target_humidity
        self.default_humidity_pad = default_humidity_pad

    @property
    def pin(self):
        return self.config.get('pin', self.default_pin)

    @property
    def humidity_pin(self):
        return self.config.get('humidity_pin', None)

    @property
    def dehumidity_pin(self):
        return self.config.get('dehumidity_pin', None)

    @property
    def cool_pin(self):
        return self.config.get('cool_pin', None)

    @property
    def target_temp_f(self):
        return self.config.get(
            'target_temp_f',
            self.default_target_temp_f)

    @property
    def temp_pad(self):
        return self.config.get('temp_pad', self.default_temp_pad)

    @property
    def min_temp_f(self):
        return self.target_temp_f - self.temp_pad

    @property
    def max_temp_f(self):
        return self.target_temp_f + self.temp_pad

    @property
    def target_humidity(self):
        return self.config.get('target_humidity', self.default_target_humidity)

    @property
    def humidity_pad(self):
        return self.config.get('humidity_pad', self.default_humidity_pad)

    @property
    def min_humidity(self):
        return self.target_humidity - self.humidity_pad

    @property
    def max_humidity(self):
        return self.target_humidity + self.humidity_pad

    def load(self):
        filepath = join(dirname(dirname(__file__)), "config.json")
        with open(filepath) as jsonfile:
            self.config = json.load(jsonfile)
