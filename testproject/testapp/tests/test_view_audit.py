from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from .base import AuditBaseTestCase
from testapp import models


class ViewAuditTest(AuditBaseTestCase):
    def setUp(self):
        super(ViewAuditTest, self).setUp()
        self.user = User.objects.create_user('lenin', 'lenin@netflix.horse', 'secure1')
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_sets_user_and_request_details(self):
        data = {
            'field1': 'no war but class war',
        }
        url = reverse('apitest')

        response = self.client.post(url, data)
        model = models.TestModelOne.objects.get(id=response.data['id'])
        change = model.audit_log.latest()

        self.assertEqual(change.action, 'CREATE')
        self.assertEqual(change.user, self.user)
