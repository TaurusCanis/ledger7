# Generated by Django 3.1.5 on 2021-03-29 23:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0054_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionrecord',
            name='description',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='budgeter.description'),
        ),
    ]