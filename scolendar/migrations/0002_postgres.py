# Generated by Django 3.0.6 on 2020-05-17 19:02

from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension


class Migration(migrations.Migration):
    dependencies = [
        ('scolendar', '0001_initial'),
    ]

    operations = [
        UnaccentExtension(),
    ]
