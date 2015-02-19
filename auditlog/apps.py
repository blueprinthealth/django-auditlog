try:
    from django.apps import AppConfig
except ImportError:
    # < django 1.7
    pass
else:
    from .default_settings import settings as audit_settings

    class AuditAppConfig(AppConfig):
        name = 'auditlog'
        verbose_name = 'Audit Log'
        label = audit_settings.APP_LABEL
