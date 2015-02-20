from __future__ import unicode_literals

from functools import partial
from django.contrib.auth import get_user_model

from .default_settings import settings
from . import signals


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
        update_kwargs = {}
        if user and isinstance(user, get_user_model()):
            update_kwargs['user'] = user
        if request.META.get('REMOTE_ADDR'):
            update_kwargs['remote_addr'] = request.META.get('REMOTE_ADDR')
        if request.META.get('REMOTE_HOST'):
            update_kwargs['remote_host'] = request.META.get('REMOTE_HOST')

        # keep the strong ref on the request, its a sane lifetime
        request._handler_func = partial(self.pre_action_handler, update_kwargs=update_kwargs)

        signals.audit_presave.connect(request._handler_func, dispatch_uid=(settings.DISPATCH_UID, request,),)

    def process_response(self, request, response):
        # disconnect signals for this request
        # runs even if change logging is disabled in case it was disabled after the signal was created
        signals.audit_presave.disconnect(dispatch_uid=(settings.DISPATCH_UID, request,))

        return response

    def pre_action_handler(self, sender, model_instance, audit_meta, update_kwargs=None, **kwargs):
        if audit_meta and getattr(audit_meta, 'audit') and update_kwargs is not None:
            audit_meta.update_additional_kwargs(update_kwargs)
