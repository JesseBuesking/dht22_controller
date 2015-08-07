import csv
from datetime import datetime
from dht22_controller.config import Config
import os


conf = Config()
conf.load()


filename = "learn_cool.csv"


def load_last_cool(default_seconds=45.):
    if not os.path.isfile(filename):
        return default_seconds

    last_seconds = default_seconds
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # only consider rows where the temperature padding is the same
            # as what's currently defined
            if float(row[3]) == conf.temp_pad:
                last_seconds = float(row[1])

    return last_seconds


def save_cool(seconds, min_temp):
    with open(filename, 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow([
            # current datetime
            datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
            # seconds used
            '{:.1f}'.format(seconds),
            # min_temp achieved
            '{:.2f}'.format(min_temp),
            # current emperature padding
            '{:.1f}'.format(conf.temp_pad)])
