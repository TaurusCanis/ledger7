from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.

class AccountBase(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(decimal_places=2, max_digits=7)
    account_type = models.CharField(max_length=30, choices=[('credit_card', 'credit_card'), ('bank_account', 'bank_account'), ('other', 'other')], default='other')

class BankAccount(models.Model):
    account_base = models.OneToOneField(AccountBase, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=30, choices=[('checking', 'Checking'),('savings', 'Savings'),('cash', 'Cash')])
    exclude_from_available_funds = models.BooleanField(default=False)

    def __str__(self):
        return self.account_base.name

    def get_balance(self):
        return self.account_base.balance

    # This needs to account for both AccountBase and BankAccount
    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in BankAccount._meta.fields]

class CreditCard(models.Model):
    account_base = models.OneToOneField(AccountBase, on_delete=models.CASCADE, null=True, blank=True)
    interest_rate = models.DecimalField(decimal_places=2, max_digits=5, default=0.0)

    def __str__(self):
        return self.account_base.name

    def get_balance(self):
        return self.account_base.balance

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in CreditCard._meta.fields]

class TransactionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.now)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    account = models.ForeignKey(AccountBase, on_delete=models.CASCADE, blank=True, null=True)
    ledger_type = models.CharField(choices=[('D','Debit'),('C','Credit')], max_length=10)
    description = models.ForeignKey("Description", on_delete=models.CASCADE, blank=True, null=True)
    exclude_from_accounting = models.BooleanField(default=False)
    transaction_type = models.CharField(max_length=20, default="other",
        choices=[
            ("E", "expense"),
            ("C", "creditcardpayment"),
            ("D", "deposit"),
            ("W", "withdrawal"),
            ("T", "transfer"),
            ("A", "adjustment"),
            ("O", "other"),
        ]
    )

    def get_type_display(self):
        if hasattr(self, "tr_expense"):
        # if self.transaction_type == "expense":
            return "Expense"
        elif hasattr(self, "ccp_bank_account") or hasattr(self, "ccp_credit_card"):
            return "Credit Card Payment"
        elif hasattr(self, "deposit"):
            print(self.deposit)
            return "Deposit"
        elif hasattr(self, "withdrawal"):
            return "Withdrawal"
        elif hasattr(self, "trf_account_to") or hasattr(self, "trf_account_from"):
            return "Transfer"
        elif hasattr(self, "adjustment"):
            return "Adjustment"
        else:
            return "MISSING"

    def delete_instance(self, user_data, ledger_type):
        if not self.exclude_from_accounting:
            user_data.set_account_balance(self.account.id, self.amount, ledger_type)

        if hasattr(self, "ccp_bank_account"):
            credit_card_payment = CreditCardPayment.objects.get(bank_account_transaction_record=self)
            ccp_credit_card_tr = credit_card_payment.credit_card_transaction_record
            if not self.exclude_from_accounting:
                user_data.set_account_balance(ccp_credit_card_tr.account.id, ccp_credit_card_tr.amount, "D")
            ccp_credit_card_tr.delete()
            credit_card_payment.delete()
        elif hasattr(self, "ccp_credit_card"):
            credit_card_payment = CreditCardPayment.objects.get(credit_card_transaction_record=self)
            ccp_bank_account_tr = credit_card_payment.bank_account_transaction_record
            if not self.exclude_from_accounting:
                user_data.set_account_balance(ccp_bank_account_tr.account.id, ccp_bank_account_tr.amount, "C")
            ccp_bank_account_tr.delete()
            credit_card_payment.delete()
        elif hasattr(self, "trf_account_to"):
            transfer_accounts = TransferAccounts.objects.get(transfer_to_transaction_record=self)
            trf_account_from = transfer_accounts.transfer_from_transaction_record
            if not self.exclude_from_accounting:
                user_data.set_account_balance(trf_account_from.account.id, trf_account_from.amount, "C")
            trf_account_from.delete()
            transfer_accounts.delete()
        elif hasattr(self, "trf_account_from"):
            transfer_accounts = TransferAccounts.objects.get(transfer_from_transaction_record=self)
            trf_account_to = transfer_accounts.transfer_to_transaction_record
            if not self.exclude_from_accounting:
                user_data.set_account_balance(trf_account_to.account.id, trf_account_to.amount, "D")
            trf_account_to.delete()
            transfer_accounts.delete()

    def get_account(self):
        if hasattr(self.account, "bankaccount"):
            return self.account.bankaccount
        elif hasattr(self.account, "creditcard"):
            return self.account.creditcard

class Expense(models.Model):
    transaction_record = models.OneToOneField(TransactionRecord, related_name="tr_expense", on_delete=models.CASCADE, default=None, null=True)
    debit_from_account = models.BooleanField(default=False)
    from_account = models.ForeignKey(AccountBase, related_name='expense_from_account', on_delete=models.CASCADE, null=True, blank=True)
    paid_to = models.CharField(max_length=100)
    note = models.CharField(max_length=250, null=True, blank=True)
    has_expense_items = models.BooleanField(default=False)
    category = models.CharField(max_length=100, default=None, null=True, blank=True)
    sub_category = models.ForeignKey("SubCategory", on_delete=models.CASCADE, blank=True, null=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Expense._meta.fields]

class ExpenseItem(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, default=None)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    note = models.CharField(max_length=250, null=True, blank=True)
    category = models.CharField(max_length=100, default=None, null=True, blank=True)
    sub_category = models.CharField(max_length=100, default=None, null=True, blank=True)
    # category = models.ForeignKey("Category", on_delete=models.CASCADE, blank=True, null=True)
    # sub_category = models.ForeignKey("SubCategory", on_delete=models.CASCADE, blank=True, null=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in ExpenseItem._meta.fields]

class ExpenseItemCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class ExpenseItemSubCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class CreditCardPayment(models.Model):
    credit_card_transaction_record = models.OneToOneField(TransactionRecord, on_delete=models.CASCADE, related_name="ccp_credit_card", default=None, null=True)
    bank_account_transaction_record = models.OneToOneField(TransactionRecord, related_name="ccp_bank_account", on_delete=models.CASCADE, default=None, null=True)

class Deposit(models.Model):
    transaction_record = models.OneToOneField(TransactionRecord, on_delete=models.CASCADE, default=None, null=True)
    note = models.CharField(max_length=250, null=True, blank=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Deposit._meta.fields]

class Withdrawal(models.Model):
    transaction_record = models.OneToOneField(TransactionRecord, on_delete=models.CASCADE, default=None, null=True)
    note = models.CharField(max_length=250, null=True, blank=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Withdrawal._meta.fields]

class TransferAccounts(models.Model):
    transfer_to_transaction_record = models.OneToOneField(TransactionRecord, on_delete=models.CASCADE, related_name="trf_account_to", blank=True, null=True)
    transfer_from_transaction_record = models.OneToOneField(TransactionRecord, on_delete=models.CASCADE, related_name="trf_account_from", blank=True, null=True)

class Adjustment(models.Model):
    transaction_record = models.OneToOneField(TransactionRecord, on_delete=models.CASCADE, default=None, null=True)
    note = models.CharField(max_length=250, null=True, blank=True)

    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in Adjustment._meta.fields]

class Description(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name
