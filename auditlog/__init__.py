__version__ = '0.3'

# use decorator or field from AuditLog on models you want audited
# by default, all requests to views are also logged (static file requests are not)
# that can be changed in settings (see the options in default_settings.py)
#
# at present, queryset.update, bulk_create, and any raw SQL operations are not logged
# except if request and SQL logging is enabled, then all queries, including those, will be logged

# import the common thing, for convienence
from .default_settings import settings
from .audit import AuditLog, ViewAudit
from .utils import disable_audit
