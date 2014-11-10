django-auditlog
================

A tool/example for django auditing (model change tracking).
Partially based on https://github.com/Atomidata/django-audit-log

It is not working in all cases in it's current state, and is a work in progress.
Currently not production ready or fully tested. I'm not sure how it handles load, 
or what kind of load it imposes. Feel free to use any or all of it.


!!TODO:
    * fix failing middleware test
    * GUI/Better admin interface, including request logging
    * customizable profile-like model for additional fields
    * m2m change logging
    * more robust testing, including multiple django versions
