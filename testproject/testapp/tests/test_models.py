from django.forms.models import model_to_dict
from django.contrib.auth.models import User

from auditlog.models import ModelChange
from auditlog.audit import AuditLog
from .base import AuditBaseTestCase
from testapp import models


class AuditChangeTest(AuditBaseTestCase):
    """Audit Logging Change Test"""

    def setUp(self):
        super(AuditChangeTest, self).setUp()
        self.user = User.objects.create(username='test_user')

    def test_post_change_state(self):
        model = models.SomeModel(field_one="x", field_two="y")
        change = ModelChange(model=model)
        change.pre_change_state = model_to_dict(model)
        change.changes = {'field_one': 'z'}
        self.assertDictContainsSubset({'field_one': 'z', 'field_two': 'y'}, change.post_change_state)


class AuditLogTestCreateChangeObjectTest(AuditBaseTestCase):
    """Audit Logging Create/Adding Tests"""

    def setUp(self):
        super(AuditLogTestCreateChangeObjectTest, self).setUp()
        self.field_vals = {'field_one': 'a', 'field_two': 'b'}
        self.test_instance = models.SomeModel(**self.field_vals)
        self.test_instance.id = 1
        self.field_vals['id'] = 1
        self.audit_log = AuditLog()
        self.audit_log.fields = self.field_vals.keys()

    def test_create_change_object_without_changes(self):
        test_instance = self.test_instance
        audit_log = self.audit_log
        old_count = ModelChange.objects.count()

        audit_log.create_change_object(test_instance, 'CREATE')
        self.assertEqual(old_count + 1, ModelChange.objects.count())

        change = ModelChange.objects.latest()

        self.assertEqual(change.model_pk, test_instance.id)
        self.assertDictEqual(change.changes, self.field_vals)

    def test_create_change_object_with_changes(self):
        test_instance = self.test_instance
        test_instance._audit_meta.pre_save = self.field_vals
        test_instance.field_one = 'c'
        audit_log = self.audit_log
        audit_log.create_change_object(test_instance, 'UPDATE')

        change = ModelChange.objects.latest()
        self.assertEqual(change.model_pk, test_instance.id)
        self.assertDictEqual(change.pre_change_state, self.field_vals)

        self.assertDictEqual(change.changes, {'field_one': 'c'})


class AuditLogTest(AuditBaseTestCase):
    """Audit Logging Tests"""
    def setUp(self):
        super(AuditLogTest, self).setUp()
        self.tm1 = models.TestModelOne.objects.create(field1="test value")
        self.tm2 = models.TestModelTwo.objects.create(field1="test value 2", tm1=self.tm1)
        self.user = User.objects.create(username='test_user')

    def test_managers(self):
        all_changes = ModelChange.objects.all()
        self.assertGreaterEqual(4, all_changes.count())
        self.assertEqual(1, self.tm1.audit_log.count())
        self.assertEqual(1, models.TestModelOne.audit_log.count())

    def test_creates_audit_log_on_create(self):
        audit_log = self.tm2.audit_log.latest()
        self.assertEqual(audit_log.action, 'CREATE')
        self.assertEqual(audit_log.model, self.tm2)

    def test_creates_audit_log_on_update(self):
        self.tm2.field1 = "some thing"
        self.tm2.save()
        audit_change = self.tm2.audit_log.get(action='UPDATE')
        self.assertEqual(audit_change.model, self.tm2)
        self.assertListEqual(audit_change.changes.keys(), ['field1'])

    def test_creates_audit_log_on_delete(self):
        self.assertEqual(self.tm2.audit_log.filter(action='DELETE').count(), 0)
        tm2_pk = self.tm2.pk
        tm1_pk = self.tm1.pk
        self.tm1.delete()
        audit_change1 = models.TestModelOne.audit_log.get(action='DELETE')
        audit_change2 = models.TestModelTwo.audit_log.get(action='DELETE')
        self.assertEqual(audit_change1.model_pk, tm1_pk)
        self.assertEqual(audit_change2.model_pk, tm2_pk)
