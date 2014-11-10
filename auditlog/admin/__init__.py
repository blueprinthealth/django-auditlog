from django.contrib import admin

from .model_admin import AuditAdmin
from auditlog.models import ModelChange

admin.site.register(ModelChange, AuditAdmin)
