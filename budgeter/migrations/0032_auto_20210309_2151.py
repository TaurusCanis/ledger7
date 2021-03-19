# Generated by Django 3.1.5 on 2021-03-09 21:51

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0031_auto_20210308_2346'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='category',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='note',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='type',
            field=models.CharField(choices=[('X', 'Expense'), ('D', 'Deposit'), ('W', 'Withdrawal'), ('T', 'Transfer'), ('A', 'Adjustment')], max_length=10),
        ),
        migrations.CreateModel(
            name='TransactionRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=7)),
                ('type', models.CharField(choices=[('X', 'Expense'), ('D', 'Deposit'), ('W', 'Withdrawal'), ('T', 'Transfer'), ('AC', 'Adjustment - Credit'), ('AD', 'Adjustment - Debit')], max_length=10)),
                ('ledger_type', models.CharField(choices=[('C', 'Credit'), ('D', 'Debit'), ('Z', 'Unknown')], default='Z', max_length=10)),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='budgeter.account')),
            ],
        ),
    ]
