from time import sleep
from datetime import datetime


__all__ = [
    "set_now",
    "now",
    "set_sleep",
    "sleep"
]


NOW = datetime.utcnow


def set_now(func):
    global NOW
    NOW = func


def now():
    return NOW()


SLEEP = sleep


def set_sleep(func):
    global SLEEP
    SLEEP = func


def sleep(duration):
    SLEEP(duration)
