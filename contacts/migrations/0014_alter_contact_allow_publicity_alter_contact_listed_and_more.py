# Generated by Django 4.0.3 on 2023-02-12 23:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0013_contact_allow_publicity_organisation_allow_publicity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='allow_publicity',
            field=models.BooleanField(help_text='Shown as a personal donor in articles, presentations etc.', null=True, verbose_name='allow publicity'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='listed',
            field=models.BooleanField(help_text='Shown as a personal donor on the website', null=True, verbose_name='listed on website'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='allow_publicity',
            field=models.BooleanField(help_text='Shown as a donor organisation in articles, presentations etc.', null=True, verbose_name='allow publicity'),
        ),
        migrations.AlterField(
            model_name='organisation',
            name='listed',
            field=models.BooleanField(help_text='Shown as a donor organisation on the website', null=True, verbose_name='listed on website'),
        ),
    ]
