# Generated by Django 3.2.4 on 2021-08-20 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0014_application_batch"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="application",
            options={
                "ordering": ("created_at",),
                "verbose_name": "application",
                "verbose_name_plural": "applications",
            },
        ),
        migrations.RemoveField(
            model_name="applicationbatch",
            name="company",
        ),
        migrations.AlterField(
            model_name="applicationbatch",
            name="proposal_for_decision",
            field=models.CharField(
                choices=[
                    ("accepted", "Decided Accepted"),
                    ("rejected", "Decided Rejected"),
                ],
                max_length=64,
                verbose_name="proposal for decision",
            ),
        ),
        migrations.AlterField(
            model_name="applicationbatch",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("awaiting_ahjo_decision", "Sent to Ahjo, decision pending"),
                    ("accepted", "Accepted in Ahjo"),
                    ("rejected", "Rejected in Ahjo"),
                    ("returned", "Returned from Ahjo without decision"),
                    ("sent_to_talpa", "Sent to Talpa"),
                    ("completed", "Processing is completed"),
                ],
                default="draft",
                max_length=64,
                verbose_name="status of batch",
            ),
        ),
    ]