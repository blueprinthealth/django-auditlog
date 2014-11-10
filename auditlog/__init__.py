# use decorator or field from AuditLog on models you want audited
# by default, all requests to views are also logged (static file requests are not)
# that can be changed in settings (see the options in default_settings.py)
#
# at present, queryset.update, bulk_create, and any raw SQL operations are not logged
# except if request and SQL logging is enabled, then all queries, including those, will be logged

from __future__ import absolute_import

default_app_config = 'auditlog.apps.AuditAppConfig'

__version__ = '0.2'
