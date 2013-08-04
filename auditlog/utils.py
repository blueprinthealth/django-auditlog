from __future__ import unicode_literals
from contextlib import contextmanager
from . import settings


def get_dict(obj):
    """ accept dict or querydict, return a dict (or the object, if None or neither) """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'dict'):
        return obj.dict()
    return obj


@contextmanager
def disable_audit():
    settings.alter_settings(CHANGE_LOGGING=False, REQUEST_LOGGING=False)
    yield
    settings.reset()
