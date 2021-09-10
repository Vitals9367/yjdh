# Generated by Django 3.2.4 on 2021-06-22 04:35

import datetime
from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0003_employee"),
    ]

    operations = [
        migrations.AlterField(
            model_name="application",
            name="company_contact_person_phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True,
                max_length=128,
                region=None,
                verbose_name="company contact person's phone number",
            ),
        ),
        migrations.AlterField(
            model_name="deminimisaid",
            name="granted_at",
            field=models.DateField(
                default=datetime.date(2021, 1, 1), verbose_name="benefit granted at"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="historicalapplication",
            name="company_contact_person_phone_number",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True,
                max_length=128,
                region=None,
                verbose_name="company contact person's phone number",
            ),
        ),
        migrations.AlterField(
            model_name="historicaldeminimisaid",
            name="granted_at",
            field=models.DateField(
                default=datetime.date(2021, 1, 1), verbose_name="benefit granted at"
            ),
            preserve_default=False,
        ),
    ]