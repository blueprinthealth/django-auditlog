This is a version of an audit log I made, since I cound't find any others that met my needs.
It is a work in progress and is probably more useful as an example or template than as a drop in solution.

Installation
------------
1. install requirements/base.txt
2. add 'audit' to installed apps
3. add 'audit.urls' to base urls file
4. add 'django.core.context_processors.request' to 'TEMPLATE_CONTEXT_PROCESSORS'
5. add audit.middleware.AuditMiddleware to middleware
