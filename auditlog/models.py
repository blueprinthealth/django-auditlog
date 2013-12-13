from __future__ import unicode_literals, absolute_import

from jsonfield import JSONField
from django.db import models
from django.contrib import contenttypes
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings


_ACTIONS = ('UPDATE', 'CREATE', 'DELETE')


class BaseAuditModel(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', blank=True, null=True)
    remote_addr = models.CharField(max_length=45, blank=True, null=True)
    remote_host = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']


@python_2_unicode_compatible
class ModelChange(BaseAuditModel):
    # original model
    model_type = models.ForeignKey(contenttypes.models.ContentType, related_name='+')
    model_pk = models.PositiveIntegerField()
    model = contenttypes.generic.GenericForeignKey('model_type', 'model_pk')

    # possibly have application specific attributes here

    # change information
    action = models.CharField(max_length=6, choices=zip(_ACTIONS, _ACTIONS), blank=False, null=False)
    pre_change_state = JSONField(blank=True, null=True)
    changes = JSONField(blank=True, null=True)

    class Meta(BaseAuditModel.Meta):
        permissions = (
            ("can_view", "Can view audit model changes and requests"),
        )

    def __str__(self):
        return "{action} -- {timestamp} [{model_type} {model_pk}]".format(
            action=self.action,
            timestamp=self.timestamp,
            model_type=self.model_type,
            model_pk=self.model_pk,
        )

    @property
    def post_change_state(self):
        post_change_state = self.pre_change_state or {}
        post_change_state.update(self.changes or {})
        return post_change_state

    @property
    def fields_changed(self):
        # there is probably a qay to do this in SQL and even index it because postgres is cool
        # but I don't know how to do that
        return self.changes.keys()

    # TODO: probably a custom manager that lets you do some nicer searches wrt what changed
