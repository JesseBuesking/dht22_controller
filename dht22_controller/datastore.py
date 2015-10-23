import csv
from dht22_controller.utils import now
from datetime import datetime
import os


import logging
log = logging.getLogger(__name__)


__all__ = [
    "load",
    "save"
]


def load(filename, default_seconds, target):
    try:
        if not os.path.isfile(filename):
            return default_seconds

        seconds = default_seconds
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                file_target = float(row[2])
                if file_target == target:
                    seconds = float(row[4])
    except Exception as e:
        log.exception(
            "exception occurred. filename=%s, default_seconds=%s, target=%s",
            filename, default_seconds, target)
        raise

    return seconds


def save(filename, starting_value, target, result, seconds):
    try:
        with open(filename, 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow([
                now().strftime('%Y-%m-%dT%H:%M:%S'),
                '{:.1f}'.format(starting_value),
                '{:.1f}'.format(target),
                '{:.2f}'.format(result),
                '{:.1f}'.format(seconds)])
    except Exception as e:
        log.exception(
            "exception occurred. filename=%s, starting_value=%s, target=%s, " +
            "result=%s, seconds=%s",
            filename, starting_value, target, result, seconds)
        raise
