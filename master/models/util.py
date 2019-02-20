import inspect
from functools import wraps

def recurse(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if len(inspect.stack()) > 25:
            print("Activated recurse limit")
            return None
        return func(*args, **kwargs)
    return wrapped


