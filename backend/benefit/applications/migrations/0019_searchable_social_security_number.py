# Generated by Django 3.2.4 on 2021-09-07 11:30

from django.db import migrations
from django.conf import settings
import encrypted_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0018_remove_unsearchable_social_security_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="encrypted_social_security_number",
            field=encrypted_fields.fields.EncryptedCharField(
                blank=True, max_length=11, verbose_name="social security number"
            ),
        ),
        migrations.AddField(
            model_name="employee",
            name="social_security_number",
            field=encrypted_fields.fields.SearchField(
                blank=True,
                db_index=True,
                encrypted_field_name="encrypted_social_security_number",
                hash_key=settings.SOCIAL_SECURITY_NUMBER_HASH_KEY,
                max_length=66,
                null=True,
            ),
        ),
    ]
