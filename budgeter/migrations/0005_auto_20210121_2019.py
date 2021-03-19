# Generated by Django 3.1.5 on 2021-01-21 20:19

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0004_auto_20210121_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='deposit',
            name='date',
            field=models.DateField(default=datetime.datetime.now),
        ),
        migrations.CreateModel(
            name='Withdrawal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=datetime.datetime.now)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=7)),
                ('note', models.CharField(blank=True, max_length=250, null=True)),
                ('from_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budgeter.account')),
            ],
        ),
    ]
