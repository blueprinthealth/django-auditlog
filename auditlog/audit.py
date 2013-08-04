from __future__ import unicode_literals
from functools import partial

from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.db.models.signals import pre_save, pre_delete
from django.db import models

from .models import ModelChange, RequestLog
from .utils import get_dict
from . import settings as audit_settings


class AuditMeta(object):

    def __init__(self):
        self.audit = True
        self.additional_kwargs = {}
        self.pre_save = None

    def update_additional_kwargs(self, updates=None, **update_kwargs):
        if updates:
            self.additional_kwargs.update(updates)
        if update_kwargs:
            self.additional_kwargs.update(update_kwargs)


class AuditLog(object):
    """
    Provides a means of accessing and controlling audit functionality on a model
    """

    # Inner classes
    class Manager(models.Manager):
        """
        an AuditLog.Manager is exposed as an instance attribute on models with an AuditLog, this is a manager
        with a queryset of all ModelChange objects for the instance, or all change objects if called on
        the model class

        """
        def __init__(self, model_type, instance=None, **kwargs):
            super(AuditLog.Manager, self).__init__(**kwargs)
            self.model = ModelChange
            self.model_type = model_type
            self.instance = instance

        def get_query_set(self):
            base_queryset = super(AuditLog.Manager, self).get_query_set().filter(model_type=self.model_type)
            if not self.instance:
                return base_queryset
            # TODO: have fallback or at least check that the model has an pk that is a positive integer
            return base_queryset.filter(model_pk=self.instance.pk)

    class Descriptor(object):
        def __init__(self, model_class):
            self.model_class = model_class

        def __get__(self, instance, owner):
            model_type = ContentType.objects.get_for_model(self.model_class)
            if instance is None:
                return AuditLog.Manager(model_type)
            return AuditLog.Manager(model_type, instance)

    # methods
    def __init__(self, exclude=[]):
        self.exclude = exclude

    def contribute_to_class(self, cls, name):
        self.attr_name = name
        self.connect_signals(cls)
        descriptor = AuditLog.Descriptor(cls)
        setattr(cls, self.attr_name, descriptor)
        setattr(cls, audit_settings.AUDIT_META_NAME, AuditMeta())

    def connect_signals(self, cls):
        models.signals.post_save.connect(self.post_save_handler, sender=cls, weak=False)
        models.signals.post_delete.connect(self.post_delete_handler, sender=cls, weak=False)
        models.signals.pre_save.connect(self.pre_save_handler, sender=cls, weak=False)
        models.signals.pre_delete.connect(self.pre_save_handler, sender=cls, weak=False)

    def build_kwargs_from_instance(self, instance):
        kwargs = {}
        # Hook to get app-sepcific kwargs to build the audit model

        return kwargs

    # also handles pre_delete
    def pre_save_handler(self, sender, instance, **kwargs):
        if kwargs.get('raw', False) or not self.should_log_change(sender, instance):
            return
        audit_meta = getattr(instance, audit_settings.AUDIT_META_NAME)
        if instance.pk is not None:
            try:
                audit_meta.pre_save = model_to_dict(sender.objects.get(pk=instance.pk), exclude=self.exclude)
            except sender.DoesNotExist:
                # this shouldn't happen unless the user manually assigns something to the pk before saving
                # TODO: log this somehow
                pass
        audit_meta.update_additional_kwargs(self.build_kwargs_from_instance(instance))

    def post_save_handler(self, sender, instance, created, **kwargs):
        if kwargs.get('raw', False) or not self.should_log_change(sender, instance):
            return
        action = 'CREATE' if created else 'UPDATE'
        self.create_change_object(instance, action)

    def post_delete_handler(self, sender, instance, **kwargs):
        if kwargs.get('raw', False) or not self.should_log_change(sender, instance):
            return
        self.create_change_object(instance, 'DELETE')

    def create_change_object(self, instance, action):
        audit_meta = getattr(instance, audit_settings.AUDIT_META_NAME)
        changes = {}
        if action == 'UPDATE' and audit_meta.pre_save:
            for field_name, new_value in model_to_dict(instance, exclude=self.exclude).items():
                old_value = audit_meta.pre_save.get(field_name)
                if old_value != new_value:
                    changes[field_name] = new_value
        elif action != 'DELETE':
            changes = model_to_dict(instance, exclude=self.exclude)

        if changes or action == 'DELETE':
            creation_kwargs = {
                'model': instance,
                'action': action,
                'pre_change_state': audit_meta.pre_save,
                'changes': changes,
            }

            request = audit_meta.additional_kwargs.get('request')
            if request and not audit_meta.additional_kwargs.get('user'):
                audit_meta.additional_kwargs['user'] = request.user

            creation_kwargs.update(audit_meta.additional_kwargs)
            ModelChange.objects.create(**creation_kwargs)

    def should_log_change(self, sender, instance):
        # hook to do more, eventually
        return audit_settings.CHANGE_LOGGING

    @classmethod
    def decorate(cls, field_name='audit_log', exclude=[]):
        """allows use as a model class decorator instead of adding as a field"""

        def add_field(klass):
            audit_log = cls(exclude)
            audit_log.contribute_to_class(klass, field_name)
            return klass

        return add_field


class ViewAudit(object):
    DISPATCH_UID_EXTRA = '_VIEW_AUDIT'

    class Mixin(object):
        """
        a django CBV mixin for logging requests and additional metadata

        if used with a Django Rest Framework view, it will also pull additional
        data from the request.
        """

        def dispatch(self, request, *args, **kwargs):
            self._audit_request = ViewAudit._pre_dispatch(self, request)
            response = super(ViewAudit.Mixin, self).dispatch(request, *args, **kwargs)
            ViewAudit._post_dispatch(self, request, response)
            del self._audit_request
            return response

        def initial(self, request, *args, **kwargs):
            # override the DRF finalize response to get additional data.
            super(ViewAudit.Mixin, self).initial(request, *args, **kwargs)
            if hasattr(self, '_audit_request'):
                self._audit_request.data = get_dict(request.DATA)
                self._audit_request.user = request.user
                self._audit_request.save()

    @classmethod
    def _presave_signal_handler(cls, sender, instance, audit_kwargs, **kwargs):
        audit_meta = getattr(instance, audit_settings.AUDIT_META_NAME, None)
        if audit_meta and getattr(audit_meta, 'audit'):
            audit_meta.update_additional_kwargs(audit_kwargs)

    @classmethod
    def _pre_dispatch(cls, view, request):
        # build partial for presave handler
        audit_request = RequestLog.objects.create_from_request(request)
        handler_function = partial(cls._presave_signal_handler, audit_kwargs={'request': audit_request})

        # connect signals
        pre_save.connect(handler_function, dispatch_uid=(audit_settings.DISPATCH_UID + cls.DISPATCH_UID_EXTRA, request), weak=False)
        pre_delete.connect(handler_function, dispatch_uid=(audit_settings.DISPATCH_UID + cls.DISPATCH_UID_EXTRA, request), weak=False)

        # return this so we can alter it if necessary
        return audit_request

    @classmethod
    def _post_dispatch(cls, view, request, response):
        # clean up signals
        pre_save.disconnect((audit_settings.DISPATCH_UID + cls.DISPATCH_UID_EXTRA, request))
        pre_delete.disconnect(dispatch_uid=(audit_settings.DISPATCH_UID + cls.DISPATCH_UID_EXTRA, request))

    @classmethod
    def decorate(cls, view_func):
        """
        a decorator for logging requests and additional data for functional views
        """

        def wrapped_view(request, *args, **kwargs):
            cls._pre_dispatch(None, request)
            response = view_func(request, *args, **kwargs)
            cls._post_dispatch(None, request, response)
            return response

        return wrapped_view
