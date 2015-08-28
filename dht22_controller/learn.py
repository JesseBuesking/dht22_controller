import logging


logging.basicConfig(filename="/tmp/dht22_controller.log", level=logging.DEBUG)


__all__ = [
    "time_boost",
    "learn"
]


def time_boost(current_time_s, starting_value, starting_threshold, pad,
    increasing=True, max_difference=0.25):
    """
    If the temperature is above the max or below the min, which happens when
    we're turning the unit on for the first time, adjust the time to account
    for the offset.
    """
    change_for = current_time_s
    # if increasing, starting value could be higher than starting threshold
    if increasing:
        diff = starting_threshold - starting_value
    else: # else the opposite
        diff = starting_value - starting_threshold

    # handle the case where we're starting far out from where we should. this
    # occurs, for example, when the freezer chest was turned on after having
    # been off for a while so we're higher than our maximum allowed temperature,
    # which is normally the temperature that we turn the freezer on at.
    if diff >= max_difference:
        # s_per should be the seconds to run for each unit change, and since
        # we typically run for double the change required, we need to divide by
        # that amount to get the number of seconds per unit change
        s_per = change_for / (pad * 2.)
        change_for += diff * s_per

    return change_for


def learn(save, current_time_s, starting_value, starting_threshold, pad, target,
    actual, debug, multiplier=3.0, increasing=True):
    """
    Learns the correct settings from the last settings used.
    """
    if not debug:
        # save what we learned from the last time
        save(current_time_s, starting_value, actual)

    # ----------------------------------------
    # learn the correct amount of time to wait
    # ----------------------------------------

    # get the difference in values
    diff = target - actual

    # multiply by 3 for a rough estimate of the amount of change in seconds
    diff = multiplier * diff

    # return the amount to change by
    return (current_time_s, diff)
