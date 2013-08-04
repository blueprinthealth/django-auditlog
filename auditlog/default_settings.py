from __future__ import unicode_literals
from django.conf import settings as global_settings

defaults = {
    'DISPATCH_UID': 'AUDIT_LOG',
    'AUDIT_META_NAME': '_audit_meta',
    'CHANGE_LOGGING': True,
    'REQUEST_LOGGING': True,
}


class SettingsContainer(object):
    def __init__(self, defaults={}, user_settings={}):
        self.defaults = defaults
        self.user_settings = user_settings
        self.changed_settings = {}

    def __getattr__(self, attr):
        if not attr in self.defaults:
            raise AttributeError("Invalid audit setting: '%s'" % attr)

        if attr in self.changed_settings:
            return self.changed_settings.get(attr)

        return self.user_settings.get(attr, self.defaults.get(attr))

    def alter_settings(self, **kwargs):
        self.changed_settings.update(kwargs)

    def reset(self):
        self.changed_settings = {}

settings = SettingsContainer(defaults, getattr(global_settings, 'AUDITLOG_SETTINGS', {}))