from rest_framework.test import APIRequestFactory
from django.db.models import signals
from django.contrib.auth.models import User

from auditlog.signals import audit_presave
from auditlog.middleware import AuditMiddleware
from .base import AuditBaseTestCase

from testapp.models import TestModelOne, TestModelTwo


class AuditMiddlewareTest(AuditBaseTestCase):
    """Audit Logging Middleware Tests"""

    def setUp(self):
        super(AuditMiddlewareTest, self).setUp()
        self.user1 = User.objects.create(username='test_user_1')
        self.user2 = User.objects.create(username='test_user_2')
        self.tm2 = TestModelTwo.objects.create(
            tm1=TestModelOne.objects.create(field1="XXXX"),
            field1="abcd",
        )
        self.request_factory = APIRequestFactory()
        self.audit_middleware = AuditMiddleware()
        request = self.request_factory.post('/', {'x': 'y'})
        request.user = self.user2
        meta = request.META.copy()
        meta['REMOTE_ADDR'] = '1.2.3.4'
        request.META = meta
        self.request = request

        self.audit_middleware.process_request(request)
        self.presave_count = len(signals.pre_save.receivers)
        self.audit_presave_count = len(audit_presave.receivers)
        self.predel_count = len(signals.pre_delete.receivers)

    def test_cleans_up_signal_handlers_on_response(self):
        self.audit_middleware.process_response(self.request, None)
        self.assertEqual(self.presave_count, len(signals.pre_save.receivers))
        self.assertEqual(self.predel_count, len(signals.pre_delete.receivers))
        self.assertEqual(self.audit_presave_count - 1, len(audit_presave.receivers))
