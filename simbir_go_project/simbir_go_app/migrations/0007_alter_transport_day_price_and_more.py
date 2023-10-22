# Generated by Django 4.2.6 on 2023-10-21 19:21

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("simbir_go_app", "0006_remove_rent_rental_time_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transport",
            name="day_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=-1,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(-1)],
            ),
        ),
        migrations.AlterField(
            model_name="transport",
            name="minute_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                default=-1,
                max_digits=12,
                null=True,
                validators=[django.core.validators.MinValueValidator(-1)],
            ),
        ),
    ]
