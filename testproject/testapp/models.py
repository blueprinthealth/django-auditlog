from django.db import models
from auditlog import audit


class SomeModel(models.Model):
    field_one = models.CharField(max_length=5)
    field_two = models.CharField(max_length=5)
    _audit_meta = audit.AuditMeta()


@audit.AuditLog.decorate()
class TestModelOne(models.Model):
    field1 = models.CharField(max_length=20)


@audit.AuditLog.decorate()
class TestModelTwo(models.Model):
    field1 = models.CharField(max_length=20)
    tm1 = models.ForeignKey('TestModelOne')
