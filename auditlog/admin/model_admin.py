from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.util import flatten_fieldsets

from .forms import AuditChangeAdminForm


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
