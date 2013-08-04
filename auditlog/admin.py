from __future__ import unicode_literals
from django.contrib import admin
from .admin_forms import AuditChangeAdminForm, RequestLogForm

from .models import ModelChange, RequestLog


class ReadOnlyAdminMixin(object):
    #def get_readonly_fields(self, *args, **kwargs):
        #if self.declared_fieldsets:
            #return flatten_fieldsets(self.declared_fieldsets)
        #else:
            #return list(set(
                #[field.name for field in self.opts.local_fields] +
                #[field.name for field in self.opts.local_many_to_many]
            #))

    def has_delete_permission(self, *args, **kwargs):
        return False

    def has_add_permission(self, *args, **kwargs):
        return False


class AuditAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('timestamp', 'action', 'model_type', 'model_pk', 'user')
    list_filter = ('model_type', 'action', 'user')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    raw_id_fields = ('request',)
    form = AuditChangeAdminForm

    fieldsets = (
        (None, {
            'fields': ('action', 'user', 'timestamp', 'request'),
        }),
        ('Model details', {
            'fields': ('model_pk', 'model_type',),
        }),
        ('Change Details', {
            'classes': ('collapse',),
            'fields': ('pre_change_state', 'changes',),
        }),
    )


class RequestAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ('path', 'timestamp', 'user', 'remote_addr', 'http_method',)
    list_filter = ('user',)
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    form = RequestLogForm


admin.site.register(ModelChange, AuditAdmin)
admin.site.register(RequestLog, RequestAdmin)
