# Generated by Django 3.1.5 on 2021-03-11 00:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0039_transactionrecord_credit_card'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='expenseitem',
            name='expense',
        ),
        migrations.AddField(
            model_name='expenseitem',
            name='transaction_record',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='budgeter.transactionrecord'),
        ),
    ]
