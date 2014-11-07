try:
    from django.apps import AppConfig
except ImportError:
    # < django 1.7
    pass
else:
    class AuditAppConfig(AppConfig):
        name = 'auditlog'
        verbose_name = 'Audit Log'
