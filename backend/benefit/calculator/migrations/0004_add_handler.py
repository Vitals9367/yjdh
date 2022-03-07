# Generated by Django 3.2.4 on 2021-11-04 05:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("calculator", "0003_changes_for_calculator_api"),
    ]

    operations = [
        migrations.AddField(
            model_name="calculation",
            name="handler",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="calculations",
                to=settings.AUTH_USER_MODEL,
                verbose_name="handler",
            ),
        ),
        migrations.AddField(
            model_name="historicalcalculation",
            name="handler",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
                verbose_name="handler",
            ),
        ),
    ]