from __future__ import unicode_literals

from jsonfield import JSONField
from django.db import models
from django.contrib import contenttypes
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.contrib.auth import get_user_model

from .utils import get_dict

_ACTIONS = ('UPDATE', 'CREATE', 'DELETE')


@python_2_unicode_compatible
class BaseAuditModel(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', blank=True, null=True)

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

    # TODO: possible hook to add custom fields to track for all models, specific to the project
    # or just add them here in the code

    # change information
    action = models.CharField(max_length=6, choices=zip(_ACTIONS, _ACTIONS), blank=False, null=False)
    pre_change_state = JSONField(blank=True, null=True)
    changes = JSONField(blank=True, null=True)

    request = models.ForeignKey('RequestLog', blank=True, null=True, related_name='model_changes')

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


class RequestManager(models.Manager):
    meta_options = (
        'CONTENT_LENGTH',
        'CONTENT_TYPE',
        'REMOTE_ADDR',
        'REMOTE_HOST',
        'REMOTE_USER',
        'REQUEST_METHOD',
        'SERVER_NAME',
        'SERVER_PORT',
    )

    def create_from_request(self, request):
        # some of the request.META fields arent't serializable, so just get ones we know about or
        # are from HTTP headers
        meta = dict((key, val) for key, val in request.META.items()
                    if key in self.meta_options or key.startswith('HTTP_'))
        create_kwargs = {
            'user': request.user if isinstance(request.user, get_user_model()) else None,
            'remote_addr': request.META.get('REMOTE_ADDR'),
            'http_method': request.method,
            'http_meta': meta,
            'http_params': get_dict(request.GET),
            'path': request.path,
        }
        if request.method == "POST":
            create_kwargs['data'] = get_dict(request.POST)

        return self.create(**create_kwargs)


@python_2_unicode_compatible
class RequestLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+', blank=True, null=True)
    remote_addr = models.TextField(help_text='accessing IP or other information')
    http_method = models.CharField(max_length=10)
    http_meta = JSONField(blank=True, null=True, help_text='header fields')
    http_params = JSONField(help_text='GET paramaters', blank=True, null=True)
    data = JSONField(help_text='POST, PUT, or PATCH data. Does not include FILES', blank=True, null=True)
    path = models.TextField()

    objects = RequestManager()

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']

    def __str__(self):
        return "{method} - {path}".format(
            method=self.http_method,
            path=self.path
        )
