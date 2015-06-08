# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelChange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('remote_addr', models.CharField(max_length=45, null=True, blank=True)),
                ('remote_host', models.TextField(null=True, blank=True)),
                ('model_pk', models.PositiveIntegerField()),
                ('action', models.CharField(max_length=6, choices=[('UPDATE', 'UPDATE'), ('CREATE', 'CREATE'), ('DELETE', 'DELETE')])),
                ('pre_change_state', jsonfield.fields.JSONField(null=True, blank=True)),
                ('changes', jsonfield.fields.JSONField(null=True, blank=True)),
                ('model_type', models.ForeignKey(related_name='+', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['-timestamp'],
                'abstract': False,
                'get_latest_by': 'timestamp',
                'permissions': (('can_view', 'Can view audit model changes and requests'),),
            },
        ),
    ]
