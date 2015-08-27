

__all__ = [
    "clip"
]


def clip(value, mini, maxi):
    return min(maxi, max(mini, value))
