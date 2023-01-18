# Generated by Django 3.2.4 on 2022-08-08 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0031_rename_summer_voucher_exception_reason_to_target_group"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employersummervoucher",
            name="target_group",
            field=models.CharField(
                blank=True,
                choices=[
                    ("primary_target_group", "primary target group"),
                    ("secondary_target_group", "secondary target group"),
                ],
                help_text="Summer voucher's target group type",
                max_length=256,
                verbose_name="summer voucher target group",
            ),
        ),
    ]