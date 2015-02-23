django-auditlog
================

Automatic change tracking for django models with some additional support for Django Rest Framework.

To use, install the app, add ```auditlog``` to your installed apps and ```auditlog.middleware.AuditMiddleware``` to the middleware classes. For use with DRF API Views, use the mixin in ```auditlog.view_audit```
