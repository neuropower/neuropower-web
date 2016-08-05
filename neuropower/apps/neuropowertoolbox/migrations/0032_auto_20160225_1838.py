# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-25 18:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('neuropowertoolbox', '0031_auto_20160225_1838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='powermodel',
            name='reqPow',
            field=models.DecimalField(blank=True, decimal_places=4, default=0, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='powermodel',
            name='reqSS',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]