django-auditlog
================

A tool/example for django auditing (model change tracking).
Partially based on https://github.com/Atomidata/django-audit-log

It is not working in all cases in it's current state, and is a work in progress.
Currently not production ready or fully tested. I'm not sure how it handles load, 
or what kind of load it imposes. Feel free to use any or all of it.

I plan to add tests (I have them, I just need to make a generic/example django project to run them in),
and possibly a setup.py to allow installation as a package if desired. 
There is also a partially complete implemetation of views to see audit information,
right now it doesn't do a lot, and may end up being scrapped.
