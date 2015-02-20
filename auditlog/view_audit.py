from .default_settings import settings
from . import signals


class DRFViewMixin(object):
    """ mixin for Django Rest Framework APIView subclasses to get
    info from the request
    """

    def initial(self, request, *args, **kwargs):
        super(DRFViewMixin, self).initial(request, *args, **kwargs)
        # at this point, DRF should have performed auth and updated the request

        def handler(sender, model_instance, audit_meta, **kwargs):
            update_kwargs = {
                'user': request.user,
            }
            if request.META.get('REMOTE_ADDR'):
                update_kwargs['remote_addr'] = request.META.get('REMOTE_ADDR')
            if request.META.get('REMOTE_HOST'):
                update_kwargs['remote_host'] = request.META.get('REMOTE_HOST')
            audit_meta.update_additional_kwargs(update_kwargs)

        request._view_audit_handler = handler
        signals.audit_presave.connect(request._view_audit_handler, dispatch_uid=(settings.DISPATCH_UID + 'drf', request))

    def finalize_response(self, request, response, *args, **kwargs):
        signals.audit_presave.disconnect(dispatch_uid=(settings.DISPATCH_UID + 'drf', request))
        return super(DRFViewMixin, self).finalize_response(request, response, *args, **kwargs)
