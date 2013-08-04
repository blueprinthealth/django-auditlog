from __future__ import unicode_literals

from functools import partial
from django.db.models.signals import pre_save, pre_delete
from django.contrib.auth import get_user_model

from . import settings


class AuditMiddleware(object):
    """
    middleware to add the user from requests to ModelChange objects.
    This is independent of request logging and can be used separately.
    """

    def process_request(self, request, *args, **kwargs):
        if not settings.CHANGE_LOGGING:
            return

        user = getattr(request, 'user', None)

        if user and not user.is_authenticated():
            user = None

        # build kwargs to pass to the signal handler
        update_kwargs = {
            'user': user if isinstance(user, get_user_model()) else None,
        }
        # other app-specific data can be added to update_kwargs here

        update_request_data = partial(self.pre_action_handler, update_kwargs=update_kwargs)

        pre_save.connect(update_request_data, dispatch_uid=(settings.DISPATCH_UID, request,), weak=False)
        pre_delete.connect(update_request_data, dispatch_uid=(settings.DISPATCH_UID, request,), weak=False)
        # TODO: add m2m changed handler?

    def process_response(self, request, response):
        # disconnect signals for this request
        # runs even if change logging is disabled in case it was disabled after the signal was created
        pre_save.disconnect(dispatch_uid=(settings.DISPATCH_UID, request,))
        pre_delete.disconnect(dispatch_uid=(settings.DISPATCH_UID, request,))

        return response

    def pre_action_handler(self, sender, instance, update_kwargs={}, **kwargs):
        audit_meta = getattr(instance, settings.AUDIT_META_NAME, None)
        if audit_meta and getattr(audit_meta, 'audit'):
            audit_meta.update_additional_kwargs(update_kwargs)
