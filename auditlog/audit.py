from __future__ import unicode_literals, absolute_import

from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from django.db import models

from .default_settings import settings as audit_settings
from .models import ModelChange


tracked_models = []


# making this a descripor that just stores a dict of instance -> meta mappings means
# that it doesn't even need to be an attr anymore. But I haven't changed that.
class AuditMeta(object):
    class InstanceMeta(object):
        def __init__(self, audit=True):
            self.additional_kwargs = {}
            self.pre_save = None
            self.audit = audit

        def update_additional_kwargs(self, updates=None, **update_kwargs):
            if updates:
                self.additional_kwargs.update(updates)
            if update_kwargs:
                self.additional_kwargs.update(update_kwargs)

        def reset(self):
            self.additional_kwargs = {}
            self.pre_save = None

    def __init__(self):
        self.audit = True

    def __get__(self, instance, owner):
        if instance is None:
            return self
        # set the attr in the instance's __dict__ which will bypass the descriptor anyhow
        return instance.__dict__.setdefault(audit_settings.AUDIT_META_NAME, self.InstanceMeta(self.audit))


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

        def get_queryset(self):
            base_queryset = super(AuditLog.Manager, self).get_queryset().filter(model_type=self.model_type)
            if not self.instance:
                return base_queryset
            # TODO: have fallback or at least check that the model has an pk that is a positive integer
            return base_queryset.filter(model_pk=self.instance.pk)

        def get_query_set(self):
            return self.get_queryset()

    class Descriptor(object):
        def __init__(self, model_class):
            self.model_class = model_class

        def __get__(self, instance, owner):
            model_type = ContentType.objects.get_for_model(self.model_class)
            if instance is None:
                return AuditLog.Manager(model_type)
            return AuditLog.Manager(model_type, instance)

    # methods
    def __init__(self, exclude=None):
        if not exclude:
            self.exclude = exclude
        else:
            self.exclude = []

    def contribute_to_class(self, cls, name):
        self.attr_name = name
        self.connect_signals(cls)
        descriptor = AuditLog.Descriptor(cls)
        setattr(cls, self.attr_name, descriptor)
        setattr(cls, audit_settings.AUDIT_META_NAME, AuditMeta())
        tracked_models.append(cls)

    def connect_signals(self, cls):
        models.signals.post_save.connect(self.post_save_handler, sender=cls, weak=False)
        models.signals.post_delete.connect(self.post_delete_handler, sender=cls, weak=False)
        models.signals.pre_save.connect(self.pre_save_handler, sender=cls, weak=False)
        models.signals.pre_delete.connect(self.pre_save_handler, sender=cls, weak=False)

    def build_kwargs_from_instance(self, instance):
        kwargs = {}

        # hook to add app specific kwargs... not sure how to allow hooking into it though
        # also really requires you to be able to add custom fields to the main audit model as well
        # can be saftely ignored

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
        meta = getattr(instance, audit_settings.AUDIT_META_NAME)
        if kwargs.get('raw', False) or not self.should_log_change(sender, instance):
            return
        action = 'CREATE' if created else 'UPDATE'
        self.create_change_object(instance, action)
        meta.reset()

    def post_delete_handler(self, sender, instance, **kwargs):
        meta = getattr(instance, audit_settings.AUDIT_META_NAME)
        if kwargs.get('raw', False) or not self.should_log_change(sender, instance):
            return
        self.create_change_object(instance, 'DELETE')
        meta.reset()

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
    def decorate(cls, field_name='audit_log', exclude=None):
        """allows use as a model class decorator instead of adding as a field"""

        def add_field(klass):
            if exclude is None:
                audit_log = cls([])
            else:
                audit_log = cls(exclude)

            audit_log.contribute_to_class(klass, field_name)
            return klass

        return add_field
