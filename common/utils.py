def nonzero(value):
    if value == 0.0:
        value += 0.0001

    return value


def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))
