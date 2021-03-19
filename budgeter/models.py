from django.db import models
from datetime import datetime

# Create your models here.

class Account(models.Model):
    name = models.CharField(max_length=100)
    balance = models.DecimalField(decimal_places=2, max_digits=7)
    type = models.CharField(max_length=30, choices=[('checking', 'Checking'),('savings', 'Savings'),('cash', 'Cash')])
    exclude_from_available_funds = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Account._meta.fields]

class CreditCard(models.Model):
    name = models.CharField(max_length=100)
    balance = models.DecimalField(decimal_places=2, max_digits=7)
    interest_rate = models.DecimalField(decimal_places=2, max_digits=5, default=0.0)

    def __str__(self):
        return self.name

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in CreditCard._meta.fields]

class TransactionRecord(models.Model):
    type = models.CharField(max_length=10, choices=[('X', 'Expense'), ('C', 'Credit Card Payment'), ('D', 'Deposit'), ('W', 'Withdrawal'), ('T', 'Transfer'), ('AC', 'Adjustment')])
    date = models.DateField(default=datetime.now)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    description = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=200, default=None, blank=True, null=True)
    sub_category = models.CharField(max_length=200, default=None, blank=True, null=True)
    ledger_type = models.CharField(max_length=10, choices=[('C', 'Credit'), ('D', 'Debit')])
    account = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True)
    credit_card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, blank=True, null=True)
    #add timestamp?
    has_expense_items = models.BooleanField(default=False)
    exclude_from_accounting = models.BooleanField(default=False)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in TransactionRecord._meta.fields]

class Transaction(models.Model):
    date = models.DateField(default=datetime.now)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    type = models.CharField(max_length=10, choices=[('X', 'Expense'), ('D', 'Deposit'), ('W', 'Withdrawal'), ('T', 'Transfer'), ('A', 'Adjustment - Credit'), ('AD', 'Adjustment - Debit')])
    ledger_type = models.CharField(max_length=10, choices=[('C', 'Credit'), ('D', 'Debit'), ('Z', 'Unknown')], default="Z")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, blank=True, null=True)
    #add timestamp?
    category = models.CharField(max_length=100, default=None, null=True, blank=True)
    note = models.CharField(max_length=250, null=True, blank=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Transaction._meta.fields]

class Expense(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    date = models.DateField()
    debit_from_account = models.BooleanField(default=False)
    from_account = models.ForeignKey(Account, related_name='expense_from_account', on_delete=models.CASCADE, null=True, blank=True)
    paid_to = models.CharField(max_length=100)
    note = models.CharField(max_length=250, null=True, blank=True)
    has_expense_items = models.BooleanField(default=False)
    transaction = models.ForeignKey(Transaction, related_name='expense_transaction', on_delete=models.CASCADE, default=None, null=True)
    category = models.CharField(max_length=100, default=None, null=True, blank=True)
    # is_recurring_expense = models.BooleanField(default=False)
    # recurring_expense_date = models.IntegerField(blank=True, null=True, default=None)
    recurring_expense = models.ForeignKey("RecurringExpense", on_delete=models.CASCADE, null=True, blank=True, default=None)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Expense._meta.fields]

class ExpenseItem(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    transaction_record = models.ForeignKey(TransactionRecord, on_delete=models.CASCADE, default=1)
    note = models.CharField(max_length=250, null=True, blank=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in ExpenseItem._meta.fields]

class RecurringExpense(models.Model):
    payment_due_date_day = models.IntegerField()
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    paid_to = models.CharField(max_length=100)
    note = models.CharField(max_length=250, null=True, blank=True)
    category = models.CharField(max_length=100, default=None, null=True, blank=True)

class Deposit(models.Model):
    date = models.DateField(default=datetime.now)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    to_account = models.ForeignKey(Account, related_name='deposit_account', on_delete=models.CASCADE)
    note = models.CharField(max_length=250, null=True, blank=True)
    transaction = models.ForeignKey(Transaction, related_name='deposit_transaction', on_delete=models.CASCADE, default=None, null=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Deposit._meta.fields]

class Withdrawal(models.Model):
    date = models.DateField(default=datetime.now)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    from_account = models.ForeignKey(Account, related_name='withdrawal_account', on_delete=models.CASCADE)
    note = models.CharField(max_length=250, null=True, blank=True)
    transaction = models.ForeignKey(Transaction, related_name='withdrawal_transaction', on_delete=models.CASCADE, null=True, default=None)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Withdrawal._meta.fields]

class Adjustment(models.Model):
    date = models.DateField(default=datetime.now)
    type = models.CharField(max_length=10, choices=[('D', 'Debit (-)'), ('C', 'Credit (+)')])
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    account = models.ForeignKey(Account, related_name='adjustment_account', on_delete=models.CASCADE)
    note = models.CharField(max_length=250, null=True, blank=True)
    transaction = models.ForeignKey(Transaction, related_name='adjustment_transaction', on_delete=models.CASCADE, default=None, null=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Adjustment._meta.fields]

class Transfer(models.Model):
    date = models.DateField(default=datetime.now)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    from_account = models.ForeignKey(Account, related_name='from_account', on_delete=models.CASCADE)
    to_account = models.ForeignKey(Account, related_name='to_account', on_delete=models.CASCADE)
    note = models.CharField(max_length=250, null=True, blank=True)
    transaction = models.ForeignKey(Transaction, related_name='transfer_transaction', on_delete=models.CASCADE, default=None, null=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Transfer._meta.fields]
