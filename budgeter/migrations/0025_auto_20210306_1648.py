# Generated by Django 3.1.5 on 2021-03-06 16:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budgeter', '0024_expense_is_recurring_expense'),
    ]

    operations = [
        migrations.RenameField(
            model_name='recurringexpense',
            old_name='payment_day',
            new_name='payment_due_date_day',
        ),
        migrations.RemoveField(
            model_name='recurringexpense',
            name='from_account',
        ),
        migrations.RemoveField(
            model_name='recurringexpense',
            name='paid',
        ),
        migrations.RemoveField(
            model_name='recurringexpense',
            name='transaction',
        ),
    ]
