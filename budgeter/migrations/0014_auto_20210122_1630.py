# Generated by Django 3.1.5 on 2021-01-22 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0013_withdrawal_transaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.CharField(choices=[('D', 'Debit (-)'), ('C', 'Credit (+)'), ('T', 'Transfer')], max_length=10),
        ),
    ]
