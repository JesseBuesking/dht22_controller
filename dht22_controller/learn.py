

__all__ = [
    "learn"
]


def learn(save, current_time_s, starting_value, starting_threshold, pad, target,
    actual, debug, multiplier=3.0, max_difference=0.25):
    """
    Learns the correct settings from the last settings used.
    """
    change_for = current_time_s
    diff = abs(starting_value - starting_threshold)

    # handle the case where we're starting far out from where we should. this
    # occurs, for example, when the freezer chest was turned on after having
    # been off for a while so we're higher than our maximum allowed temperature,
    # which is normally the temperature that we turn the freezer on at.
    if diff >= max_difference:
        # s_per should be the seconds to run for each unit change, and since
        # we typically run for double the change required, we need to divide by
        # that amount to get the number of seconds per unit change
        s_per = change_for / (pad * 2.)
        change_for = diff * s_per

    if not debug:
        # save what we learned from the last time
        save(change_for, starting_value, actual)

    # ----------------------------------------
    # learn the correct amount of time to wait
    # ----------------------------------------

    # get the difference in values
    diff = target - actual

    # multiply by 3 for a rough estimate of the amount of change in seconds
    diff = multiplier * diff

    # return the amount to change by
    return (change_for, diff)
