import csv
from datetime import datetime
from dht22_controller.config import Config
import os


conf = Config()
conf.load()


def load_last_cool(default_seconds=45.):
    return load_last("learn-cool.csv", default_seconds)


def load_last_heat(default_seconds=45.):
    return load_last("learn-heat.csv", default_seconds)


def load_last(filename, default_seconds):
    if not os.path.isfile(filename):
        return default_seconds

    last_seconds = default_seconds
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            target = float(row[3])
            if target == conf.target_temp_f:
                last_seconds = float(row[1])

    return last_seconds


def save(filename, seconds, target_temp, starting_temp, resulting_temp):
    with open(filename, 'a') as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow([
            # current datetime
            datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
            # seconds used
            '{:.1f}'.format(seconds),
            # resultant temperature
            '{:.2f}'.format(resulting_temp),
            # target
            '{:.1f}'.format(target_temp),
            # starting temp
            '{:.1f}'.format(starting_temp)])


def save_cool(seconds, starting_temp, resulting_temp):
    save("learn-cool.csv", seconds, conf.min_temp_f, starting_temp, resulting_temp)


def save_heat(seconds, starting_temp, resulting_temp):
    save("learn-heat.csv", seconds, conf.max_temp_f, starting_temp, resulting_temp)
