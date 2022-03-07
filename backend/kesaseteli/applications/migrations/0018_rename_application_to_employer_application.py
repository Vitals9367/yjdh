# Generated by Django 3.2.4 on 2021-12-30 08:36

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("companies", "0005_remove_company_eauth_profile"),
        ("applications", "0017_refactor_school"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Application",
            new_name="EmployerApplication",
        ),
        migrations.RenameModel(
            old_name="HistoricalApplication",
            new_name="HistoricalEmployerApplication",
        ),
    ]