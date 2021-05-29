from django.forms import ModelForm, DateInput
from budgeter.models import (Expense, AccountBase, BankAccount, CreditCard, CreditCardPayment,
    TransactionRecord, Description, Category, SubCategory, Deposit, Withdrawal, TransferAccounts,
    Adjustment, ExpenseItemCategory, ExpenseItemSubCategory, ExpenseItem)
from django import forms
from datetime import datetime, timedelta
from django.db.models import Q

class CreateAccountBaseForm(forms.Form):
    name = forms.CharField(max_length=100)
    balance = forms.DecimalField(decimal_places=2, max_digits=7)

class CreateBankAccountForm(CreateAccountBaseForm):
    name = forms.CharField(max_length=100)
    balance = forms.DecimalField(decimal_places=2, max_digits=7)
    type = forms.ChoiceField(choices=[('checking', 'Checking'),('savings', 'Savings'),('cash', 'Cash')])
    exclude_from_available_funds = forms.BooleanField(required=False)

class CreateCreditCardForm(CreateAccountBaseForm):
    name = forms.CharField(max_length=100)
    balance = forms.DecimalField(decimal_places=2, max_digits=7)
    interest_rate = forms.DecimalField(decimal_places=2, max_digits=5)

class TransactionRecordBaseForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class' : 'form-control'}))
    amount = forms.DecimalField(decimal_places=2, max_digits=7, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    # account = forms.CharField(required=False, widget=forms.HiddenInput())
    account = forms.ChoiceField(choices=[('','')], widget=forms.RadioSelect())
    #add timestamp?
    exclude_from_accounting = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class":"form-check-input", "type":"checkbox"}))
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={'class' : 'form-control'}))

    def get_account(self, user_data, account_id=None):
        print("GET ACCOUNT - self.cleaned_data['account']: ", self.cleaned_data['account'])
        if not account_id:
            return user_data.get_account_base(self.cleaned_data['account'])
        else:
            return user_data.get_account_base(account_id)

    def create_transaction_record(self, user_data, ledger_type, transaction_type, account_id=None):

        account = self.get_account(user_data, account_id)
        print("ACCOUNT: ", account)
        print("ledger_type: ", ledger_type)

        if self.cleaned_data['exclude_from_accounting'] == False:
            self.update_account_balances(user_data, ledger_type, self.cleaned_data['amount'], account.id)

        return TransactionRecord.objects.create(
            user = user_data.user,
            date = self.cleaned_data['date'],
            amount = self.cleaned_data['amount'],
            account = account,
            ledger_type = ledger_type,
            description = Description.objects.get_or_create(
                user = user_data.user,
                name = self.cleaned_data['description']
            )[0],
            transaction_type=transaction_type,
            exclude_from_accounting=self.cleaned_data['exclude_from_accounting']
        )

    def update_transaction_record(self, transaction_record, user_data, ledger_type, transaction_type):

        if transaction_type == "creditcardpayment" or transaction_type == "transfer":
            if transaction_type == "creditcardpayment":
                account_1 = int(self.cleaned_data['account'])
                account_2 = int(self.cleaned_data['credit_card'])
            if transaction_type == "transfer":
                account_1 = int(self.cleaned_data['transfer_from_account'])
                account_2 = int(self.cleaned_data['account'])
            account = self.get_account(user_data, account_1)
            if ledger_type == "D":

                if transaction_record.account.id != account_1:
                    self.reverse_ledger(user_data, transaction_record, ledger_type, transaction_type, account, transaction_record.account)

                elif transaction_record.amount != self.cleaned_data['amount']:
                    self.reverse_ledger(user_data, transaction_record, ledger_type, transaction_type, account)
            else:
                account = self.get_account(user_data, account_id=transaction_record.account.id)
                if transaction_record.account.id != account_2:
                    account = self.get_account(user_data, account_2)
                    self.reverse_ledger(user_data, transaction_record, ledger_type, transaction_type, account, transaction_record.account)

                elif transaction_record.amount != self.cleaned_data['amount']:
                    self.reverse_ledger(user_data, transaction_record, ledger_type, transaction_type, account)

        elif transaction_type == "adjustment":
            account = self.get_account(user_data)

            if transaction_record.ledger_type == "D":
                rev_ledger = "C"
            else:
                rev_ledger = "D"
            self.update_account_balances(user_data, rev_ledger, transaction_record.amount, transaction_record.account.id)
            self.update_account_balances(user_data, ledger_type, self.cleaned_data['amount'], self.cleaned_data['account'])

        else:
            account = self.get_account(user_data)

            if transaction_record.account.id != int(self.cleaned_data['account']):
                self.reverse_ledger(user_data, transaction_record, ledger_type, transaction_type, account, transaction_record.account)

            elif transaction_record.amount != self.cleaned_data['amount']:
                self.reverse_ledger(user_data, transaction_record, ledger_type, transaction_type, account)

        transaction_record.date = self.cleaned_data['date']
        transaction_record.amount = self.cleaned_data['amount']
        transaction_record.account = account
        transaction_record.ledger_type = ledger_type
        transaction_record.description = Description.objects.get_or_create(
            user = user_data.user,
            name = self.cleaned_data['description']
        )[0]
        transaction_record.transaction_type=transaction_type
        transaction_record.exclude_from_accounting=self.cleaned_data['exclude_from_accounting']
        transaction_record.save()

    def update_account_balances(self, user_data, ledger_type, amount, account_id):
        print("update_account_balances")
        user_data.set_account_balance(account_id, amount, ledger_type)
        return

    def reverse_ledger(self, user_data, transaction_record, ledger_type, transaction_type, account, account_2=None):
        print("REV")
        self.update_account_balances(user_data, ledger_type, self.cleaned_data['amount'], account.id)

        if ledger_type == "D":
            ledger_type = "C"
        else:
            ledger_type = "D"

        if account_2:
            account = account_2

        self.update_account_balances(user_data, ledger_type, transaction_record.amount, account.id)

class TransactionRecordExpenseForm(TransactionRecordBaseForm):
    category = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    sub_category = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    has_expense_items = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class":"form-check-input", "type":"checkbox"}))
    # debit_from_account = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class":"form-check-input", "type":"checkbox"}))
    paid_to = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    note = forms.CharField(required=False, max_length=250, widget=forms.TextInput(attrs={'class' : 'form-control'}))

    def __init__(self, *args, **kwargs):
        print("ARGS: ", args)
        print("KWARGS: ", kwargs)

        user_data = kwargs.pop('user_data')
        view_type = kwargs.pop('view_type')
        super().__init__(*args, **kwargs)

        if view_type == "update":
            self.initial['account'] = self.initial['tr_expense'].transaction_record.account.id

        self.choices = user_data.get_all_account_bases().order_by('account_type').values_list("id", "name")
        self.fields['account'].choices = self.choices

    def create_record(self, user_data, ledger_type='D'):
        new_transaction_record = super().create_transaction_record(user_data, ledger_type="D", transaction_type="expense")
        return Expense.objects.create(
            transaction_record = new_transaction_record,
            # debit_from_account = self.cleaned_data['debit_from_account'],
            paid_to = self.cleaned_data['paid_to'],
            note = self.cleaned_data['note'],
            has_expense_items = self.cleaned_data['has_expense_items'],
            category = Category.objects.get_or_create(
                user = user_data.user,
                name = self.cleaned_data['category']
            )[0],
            sub_category = SubCategory.objects.get_or_create(
                user = user_data.user,
                name = self.cleaned_data['sub_category']
            )[0]
        )

    def update_instance(self, transaction_record, user_data):
        super().update_transaction_record(transaction_record, user_data, ledger_type="D", transaction_type="expense")

class ExpenseItemForm(forms.Form):
    expense_id = forms.CharField(widget=forms.HiddenInput())
    name = forms.CharField(max_length=250, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    amount = forms.DecimalField(decimal_places=2, max_digits=7, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    note = forms.CharField(required=False, max_length=250, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    category = forms.CharField(required=False, max_length=250, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    sub_category = forms.CharField(required=False, max_length=250, widget=forms.TextInput(attrs={'class' : 'form-control'}))

    def create_expense_item(self, user_data, expense_id):
        ExpenseItem.objects.create(
            expense = Expense.objects.get(id=expense_id),
            name = self.cleaned_data['name'],
            amount = self.cleaned_data['amount'],
            note = self.cleaned_data['note'],
            category = ExpenseItemCategory.objects.get_or_create(
                user = user_data.user,
                name = self.cleaned_data['category']
            )[0],
            sub_category = ExpenseItemSubCategory.objects.get_or_create(
                user = user_data.user,
                name = self.cleaned_data['sub_category']
            )[0]
        )

class TransactionRecordCreditCardPaymentForm(TransactionRecordBaseForm):
    # credit_card = forms.CharField(widget=forms.HiddenInput())
    credit_card = forms.ChoiceField(choices=[('','')], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        user_data = kwargs.pop('user_data')
        view_type = kwargs.pop('view_type')
        super().__init__(*args, **kwargs)
        print("self.initial: ", self.initial)
        print("view_type: ", view_type)

        if view_type == "update":
            ccp_object = self.get_creditcardpayment_object()

            self.initial['credit_card'] = ccp_object.credit_card_transaction_record.account.id
            self.initial['account'] = ccp_object.bank_account_transaction_record.account.id

        self.choices = user_data.account_bases_bank_accounts.values_list("id", "name")
        self.fields['account'].choices = self.choices
        self.fields['credit_card'].choices = user_data.account_bases_credit_cards.values_list("id", "name")

    def get_creditcardpayment_object(self):
        if self.initial['ledger_type'] == "D":
            return CreditCardPayment.objects.get(bank_account_transaction_record_id=self.initial['id'])
        else:
            return CreditCardPayment.objects.get(credit_card_transaction_record_id=self.initial['id'])

    def create_record(self, user_data):
        return CreditCardPayment.objects.create(
            credit_card_transaction_record = super().create_transaction_record(user_data, ledger_type="C", transaction_type="creditcardpayment", account_id=self.cleaned_data['credit_card']),
            bank_account_transaction_record = super().create_transaction_record(user_data, ledger_type="D", transaction_type="creditcardpayment")
        )

    def update_instance(self, transaction_record, user_data):
        ccp_object = self.get_creditcardpayment_object()

        ccp_bankaccount = ccp_object.bank_account_transaction_record
        ccp_creditcard = ccp_object.credit_card_transaction_record

        print("ccp_bankaccount: ", ccp_bankaccount.account)
        print("ccp_creditcard: ", ccp_creditcard.account)

        super().update_transaction_record(ccp_bankaccount, user_data, ledger_type=ccp_bankaccount.ledger_type, transaction_type="creditcardpayment")
        print("************IN_BETWEEN**************")
        super().update_transaction_record(ccp_creditcard, user_data, ledger_type=ccp_creditcard.ledger_type, transaction_type="creditcardpayment")

class TransactionRecordDepositForm(TransactionRecordBaseForm):

    def __init__(self, *args, **kwargs):

        user_data = kwargs.pop('user_data')
        view_type = kwargs.pop('view_type')
        super().__init__(*args, **kwargs)

        self.choices = user_data.account_bases_bank_accounts.values_list("id", "name")
        self.fields['account'].choices = self.choices

    def create_record(self, user_data):
        return Deposit.objects.create(
            transaction_record = super().create_transaction_record(user_data, ledger_type="C", transaction_type="deposit")
        )

    def update_instance(self, transaction_record, user_data):
        super().update_transaction_record(transaction_record, user_data, ledger_type="C", transaction_type="deposit")


class TransactionRecordWithdrawalForm(TransactionRecordBaseForm):

    def __init__(self, *args, **kwargs):

        user_data = kwargs.pop('user_data')
        view_type = kwargs.pop('view_type')
        super().__init__(*args, **kwargs)

        self.choices = user_data.account_bases_bank_accounts.values_list("id", "name")
        self.fields['account'].choices = self.choices

    def create_record(self, user_data):
        return Withdrawal.objects.create(
            transaction_record = super().create_transaction_record(user_data, ledger_type="D", transaction_type="withdrawal")
        )

    def update_instance(self, transaction_record, user_data):
        super().update_transaction_record(transaction_record, user_data, ledger_type="D", transaction_type="withdrawal")

class TransactionRecordTransferForm(TransactionRecordBaseForm):
    # transfer_from_account = forms.CharField(widget=forms.HiddenInput())
    transfer_from_account = forms.ChoiceField(choices=[('','')], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):

        user_data = kwargs.pop('user_data')
        view_type = kwargs.pop('view_type')
        super().__init__(*args, **kwargs)

        if view_type == "update":
            if self.initial['ledger_type'] == "D":
                ta_object = TransferAccounts.objects.get(transfer_from_transaction_record_id=self.initial['id'])
            else:
                ta_object = TransferAccounts.objects.get(transfer_to_transaction_record_id=self.initial['id'])

            self.initial['transfer_from_account'] = ta_object.transfer_from_transaction_record.account.id
            self.initial['account'] = ta_object.transfer_to_transaction_record.account.id

        self.choices = user_data.account_bases_bank_accounts.values_list("id", "name")
        self.fields['account'].choices = self.choices
        self.fields['transfer_from_account'].choices = self.choices

        print("SELF: ", self)

    def create_record(self, user_data):
        return TransferAccounts.objects.create(
            transfer_from_transaction_record = super().create_transaction_record(user_data, ledger_type="D", account_id=self.cleaned_data['transfer_from_account'], transaction_type="transfer"),
            transfer_to_transaction_record = super().create_transaction_record(user_data, ledger_type="C", transaction_type="transfer")
        )

    def get_tansfer_object(self):
        if self.initial['ledger_type'] == "D":
            return TransferAccounts.objects.get(transfer_from_transaction_record_id=self.initial['id'])
        else:
            return TransferAccounts.objects.get(transfer_to_transaction_record_id=self.initial['id'])

    def update_instance(self, transaction_record, user_data):
        transfer_object = self.get_tansfer_object()

        transfer_from_transaction_record = transfer_object.transfer_from_transaction_record
        transfer_to_transaction_record = transfer_object.transfer_to_transaction_record

        print("transfer_from_transaction_record: ", transfer_from_transaction_record.account)
        print("transfer_to_transaction_record: ", transfer_to_transaction_record.account)

        super().update_transaction_record(transfer_from_transaction_record, user_data, ledger_type=transfer_from_transaction_record.ledger_type, transaction_type="transfer")
        print("************IN_BETWEEN**************")
        super().update_transaction_record(transfer_to_transaction_record, user_data, ledger_type=transfer_to_transaction_record.ledger_type, transaction_type="transfer")


class TransactionRecordAdjustmentForm(TransactionRecordBaseForm):
    ledger_type = forms.CharField(widget=forms.RadioSelect(choices=[('C', 'Add Funds'), ('D', 'Remove Funds')]))

    def __init__(self, *args, **kwargs):

        user_data = kwargs.pop('user_data')
        view_type = kwargs.pop('view_type')
        super().__init__(*args, **kwargs)

        if view_type == "update":
            adjustment_object = Adjustment.objects.get(transaction_record_id=self.initial['id'])

            self.initial['account'] = adjustment_object.transaction_record.account.id

        self.choices = user_data.account_bases_bank_accounts.values_list("id", "name")
        self.fields['account'].choices = self.choices

    def create_record(self, user_data):
        return Adjustment.objects.create(
            transaction_record = super().create_transaction_record(user_data, ledger_type=self.cleaned_data['ledger_type'], transaction_type="adjustment")
        )

    def update_instance(self, transaction_record, user_data):
        super().update_transaction_record(transaction_record, user_data, ledger_type=self.cleaned_data['ledger_type'], transaction_type="adjustment")


class AccountSearchForm(forms.Form):

    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class' : 'form-control'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class' : 'form-control'}), required=False)
    transaction_type = forms.MultipleChoiceField(choices=[('deposit', 'Deposit'),('withdrawal', 'Withdrawal'),('expense', 'Expense'),('transfer', 'Transfer'), ('creditcardpayment', 'Credit Card Payment'), ('adjustment', 'Adjustment')], widget=forms.SelectMultiple(attrs={'class':'form-control'}), required=False)
    account = forms.MultipleChoiceField(widget=forms.SelectMultiple(attrs={'class':'form-control'}), required=False, choices=[" ", " "])

    def __init__(self, *args, **kwargs):
        print("ARGS: ", args)
        print("KWARGS: ", kwargs)

        user_data = kwargs.pop('user_data')
        super().__init__(*args, **kwargs)

        if len(args) == 0:
            end_date = datetime.today()
            start_date = end_date.date() - timedelta(days=7)
            start_date = start_date.strftime('%Y-%m-%d')
            self.fields['start_date'].initial = start_date
            self.fields['end_date'].initial = end_date
        self.choices = user_data.get_all_account_bases().values_list("id", "name")
        self.fields['account'].choices = self.choices
