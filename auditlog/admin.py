from __future__ import absolute_import
from __future__ import unicode_literals

import json
from django.contrib import admin
from django.contrib.admin.util import flatten_fieldsets
from django import forms
from django.contrib.auth import get_user_model
from django.utils.html import escape
from django.utils.safestring import mark_safe

from auditlog.models import ModelChange


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


class ReadOnlyAdminMixin(object):
    # note: the dict display widget doesn't work if the field is readonly
    def get_readonly_fields(self, *args, **kwargs):
        if self.declared_fieldsets:
            return flatten_fieldsets(self.declared_fieldsets)
        else:
            return list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]
            ))

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, *args, **kwargs):
        return False


class AuditAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'model_type', 'model_pk', 'user', 'remote_addr', 'remote_host')
    list_filter = ('model_type', 'action', 'user',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    form = AuditChangeAdminForm

    fieldsets = (
        (None, {
            'fields': ('action', 'user', 'timestamp', 'remote_addr', 'remote_host'),
        }),
        ('Model details', {
            'fields': ('model_pk', 'model_type',),
        }),
        ('Change Details', {
            'classes': ('collapse',),
            'fields': ('pre_change_state', 'changes',),
        }),
    )


admin.site.register(ModelChange, AuditAdmin)
