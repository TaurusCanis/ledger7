# Generated by Django 3.1.5 on 2021-01-22 00:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0008_auto_20210122_0012'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adjustment',
            old_name='from_account',
            new_name='account',
        ),
    ]
