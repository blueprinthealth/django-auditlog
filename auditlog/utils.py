from __future__ import unicode_literals
import functools
from . import settings


def get_dict(obj):
    """ accept dict or querydict, return a dict (or the object, if None or neither) """
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'dict'):
        return obj.dict()
    return obj


class DisableAuditContextManager(object):
    """ dual-purpose decorator and context manager """
    def __call__(self, func):
        @functools.wraps(func)
        def decorated_func(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return decorated_func

    def __enter__(self):
        settings.alter_settings(CHANGE_LOGGING=False, REQUEST_LOGGING=False)

    def __exit__(self,*args):
        settings.reset()


disable_audit = DisableAuditContextManager()
