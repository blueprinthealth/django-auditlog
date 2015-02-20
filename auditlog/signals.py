from django.dispatch import Signal


audit_presave = Signal(providing_args=['model_instance', 'audit_meta'])
