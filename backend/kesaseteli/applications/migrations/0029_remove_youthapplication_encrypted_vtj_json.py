# Generated by Django 3.2.4 on 2022-05-06 12:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0028_add_encrypted_handler_and_original_vtj_json"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="youthapplication",
            name="encrypted_vtj_json",
        ),
    ]