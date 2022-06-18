# Generated by Django 4.0.3 on 2022-04-23 02:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supply_demand', '0026_remove_offeritem_claimed_by_alter_offeritem_notes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offeritem',
            name='model',
            field=models.CharField(max_length=100, verbose_name='model'),
        ),
        migrations.AlterField(
            model_name='requestitem',
            name='model',
            field=models.CharField(blank=True, help_text='Either an explicit model or a description of the required features', max_length=100, verbose_name='model'),
        ),
    ]