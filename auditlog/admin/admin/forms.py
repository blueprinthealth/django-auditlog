from __future__ import unicode_literals
import json

from django import forms
from django.contrib.auth import get_user_model
from django.utils.html import escape
from django.utils.safestring import mark_safe

from audit.models import ModelChange


# do this to make sure the user class is initialized so we can make a form field with it
get_user_model()


class DictionaryDisplayWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        value = json.loads(value)
        if value:
            rows = []
            for key, val in value.items():
                rows.append('<tr><td>{key}</td><td>{val}</td></tr>'.format(
                    key=escape(key),
                    val=escape(val),
                ))
            return mark_safe("<table border='1'>{}</table>".format('\n'.join(rows)))


class AuditChangeAdminForm(forms.ModelForm):
    timestamp = forms.DateTimeField()
    pre_change_state = forms.Field(widget=DictionaryDisplayWidget)
    changes = forms.Field(widget=DictionaryDisplayWidget)

    class Meta:
        model = ModelChange
        fields = ('timestamp', 'user', 'remote_addr', 'remote_host',
                  'model_type', 'model_pk', 'action', 'pre_change_state', 'changes',)

