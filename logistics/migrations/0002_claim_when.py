# Generated by Django 4.0.3 on 2022-04-20 22:11

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("logistics", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="claim",
            name="when",
            field=models.DateField(default=django.utils.timezone.now, verbose_name="when"),
            preserve_default=False,
        ),
    ]
