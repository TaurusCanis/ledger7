from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from budgeter.models import Account, Expense, ExpenseItem, Deposit, Withdrawal, Adjustment, Transfer, Transaction, TransactionRecord, RecurringExpense, CreditCard
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime
from django import forms
from budgeter.forms import TransactionRecordBaseForm, TransactionRecordExpenseForm, TransactionRecordTransferForm, TransactionRecordCreditCardPaymentForm
from django.forms import modelform_factory
from django.forms.models import model_to_dict

class IndexView(TemplateView):
    template_name = 'budgeter/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        accounts = Account.objects.all()
        transactions_list = Transaction.objects.all().order_by('-date')
        # last_five_transactions = Transaction.objects.all().order_by('-date')[:5]
        # context['transactions'] = last_five_transactions

        transaction_records_list = TransactionRecord.objects.all().order_by('-date')[:10]
        print("transaction_records_list: ", transaction_records_list)
        if transaction_records_list.count() != 0:
            print("transaction_records_list[0].amount: ", transaction_records_list[0].amount)
            print("transactions_list.aggregate(Sum('amount'))['amount__sum']: ", transactions_list.aggregate(Sum('amount'))['amount__sum'])
        context['transaction_records_list'] = transaction_records_list

        credit_cards = CreditCard.objects.all()
        context['credit_cards'] = credit_cards

        upcoming_expenses = RecurringExpense.objects.all()
        context['upcoming_expenses'] = upcoming_expenses
        print("*****upcoming_expenses: ", upcoming_expenses)
        context['accounts'] = accounts
        # context['transactions'] = [self.format_transaction(transaction) for transaction in transactions_list]

        if credit_cards.count() == 0:
            context['credit_cards_total'] = 0
        else:
            context['credit_cards_total'] = round(credit_cards.aggregate(Sum('balance'))['balance__sum'], 2)

        if transaction_records_list.count() == 0:
            context['transactions_total_debits'] = 0
            # context['transactions_total_credits'] = 0
        else:
            context['transactions_total_debits'] = round(transaction_records_list.aggregate(Sum('amount'))['amount__sum'], 2)
            # context['transactions_total_credits'] = round(transaction_records_list.filter(ledger_type='C').aggregate(Sum('amount'))['amount__sum'], 2)

        if accounts.count() == 0:
            context['total_available_funds'] = 0
        else:
            if credit_cards.count() == 0:
                context['total_available_funds'] = round(accounts.filter(exclude_from_available_funds=False).aggregate(Sum('balance'))['balance__sum'], 2)
            else:
                context['total_available_funds'] = round(accounts.filter(exclude_from_available_funds=False).aggregate(Sum('balance'))['balance__sum'], 2) - round(credit_cards.aggregate(Sum('balance'))['balance__sum'], 2)


        # print("context: ", context)
        context['base_template'] = 'budgeter/no_base.html'
        return context

    def format_transaction(self, transaction):
        print("transaction.id: ", transaction.id)
        if transaction.type is 'X':
            return { "transaction": transaction, "transaction_type": Expense.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'D':
            return { "transaction": transaction, "transaction_type": Deposit.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'W':
            return { "transaction": transaction, "transaction_type": Withdrawal.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'T':
            return { "transaction": transaction, "transaction_type": Transfer.objects.get(transaction_id=transaction.id) }
        else:
            return { "transaction": transaction, "transaction_type": Adjustment.objects.get(transaction_id=transaction.id) }

def index(request):
    return render(request, "budgeter/index.html")

class CreateAccountView(CreateView):
    model = Account
    fields = '__all__'
    success_url = '/budgeter/'

class AccountUpdateView(UpdateView):
    model = Account
    fields = '__all__'
    success_url = '/budgeter/'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['balance'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['type'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['exclude_from_available_funds'].widget = forms.CheckboxInput(attrs={'class':'form-check-input'})
        return form

class AccountListView(ListView):
    model = Account
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['total_available_funds'] = round(super().get_queryset().aggregate(Sum('balance'))['balance__sum'], 2)
        context['standalone'] = True
        context['base_template'] = 'budgeter/base.html'
        return context

class AccountDetailView(DetailView):
    model = Account

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("self.object.id: ", self.object.id)
        transaction_records_list = TransactionRecord.objects.filter(account=self.object.id).order_by('date')
        print("transaction_records_list: ", transaction_records_list)
        context['transaction_records_list'] = transaction_records_list
        if transaction_records_list.count() == 0:
            context['transaction_records_total'] = 0
        else:
            context['transaction_records_total'] = round(transaction_records_list.aggregate(Sum('amount'))['amount__sum'], 2)
        context['base_template'] = 'budgeter/no_base.html'
        return context

class AccountDeleteView(DeleteView):
    model = Account

    def get_success_url(self):
        return reverse('index')

class CreateCreditCardView(CreateView):
    model = CreditCard
    fields = '__all__'
    success_url = '/budgeter/'

class UpdateCreditCardView(UpdateView):
    model = CreditCard
    fields = '__all__'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['balance'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['interest_rate'].widget = forms.TextInput(attrs={'class':'form-control'})
        return form

    def get_success_url(self):
        return reverse('index')

class DeleteCreditCardView(DeleteView):
    model = CreditCard

    def get_success_url(self):
        return reverse('index')

class CreditCardDetailView(DetailView):
    model = CreditCard

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_template'] = 'budgeter/no_base.html'
        transaction_records_list = TransactionRecord.objects.filter(credit_card=self.object.id).order_by('date')
        for tr in transaction_records_list:
            for k, v in model_to_dict(tr).items():
                print("k: ", k, "v: ", v)
            print("*********************")
        context['transaction_records_list'] = transaction_records_list
        if transaction_records_list.count() == 0:
            context['transaction_records_total'] = 0
        else:
            context['transaction_records_total'] = round(transaction_records_list.aggregate(Sum('amount'))['amount__sum'], 2)

        return context

class CreditCardListView(ListView):
    model = CreditCard

class TransactionRecordOptions(TemplateView):
    template_name = 'budgeter/transaction_record_options.html'

## Should probably create separate views for each TransactionRecord Form

class CreateTransactionRecord(FormView):
    template_name = 'budgeter/transactionrecord_form.html'
    form_class = TransactionRecordBaseForm

    # model = TransactionRecord
    # exclude = None

    def get_form(self, form_class=None):
        print("kwargs['slug']: ", self.kwargs['slug'])
        form = super().get_form(form_class)
        form.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
        print("Account.objects.values_list('id', 'name'): ", list(Account.objects.values_list('id', 'name')))



        # if self.kwargs['slug'] == 'transfer':
        #     form.fields['transfer_to_account'].widget = forms.CharField()
        print("form.fields: ", form.fields)

        credit_card_choice_list = [
            ('', ''),
        ]
        credit_card_choice_list.extend(list(CreditCard.objects.values_list('id', 'name')))

        account_choice_list = [
            ('', ''),
        ]
        account_choice_list.extend(list(Account.objects.values_list('id', 'name')))

        print("credit_card_choice_list: ", credit_card_choice_list)

        self.exclude = ['type', 'ledger_type', 'has_expense_items', 'transfer_to_account']
        if self.kwargs['slug'] in ['expense', 'credit_card_payment']:
            # form.fields['credit_card'] = forms.ChoiceField(choices=credit_card_choice_list)
            # form.fields['account'] = forms.ChoiceField(choices=account_choice_list)
            self.exclude.remove('has_expense_items')
        if self.kwargs['slug'] == 'deposit' or self.kwargs['slug'] == 'withdrawal' or self.kwargs['slug'] == 'transfer' or self.kwargs['slug'] == 'adjustment':
            self.exclude.append('credit_card')
            # form.fields['account'] = forms.ChoiceField(choices=account_choice_list)
        if self.kwargs['slug'] == 'transfer':
            print("transfer")
            self.exclude.remove('transfer_to_account')
            # form.fields['transfer_to_account'] = forms.ChoiceField(choices=account_choice_list)
        return form

    def get_form_class(self):
        print("get_form_class")
        form_class = super().get_form_class()

        self.exclude = ['type', 'ledger_type', 'has_expense_items', 'transfer_to_account']
        if self.kwargs['slug'] == 'expense':
            self.exclude.remove('has_expense_items')
            form_class = TransactionRecordExpenseForm
        if self.kwargs['slug'] == 'deposit' or self.kwargs['slug'] == 'withdrawal' or self.kwargs['slug'] == 'transfer' or self.kwargs['slug'] == 'adjustment':
            self.exclude.append('credit_card')
        if self.kwargs['slug'] == 'credit_card_payment':
            print("CREDIT CARD")
            form_class = TransactionRecordCreditCardPaymentForm
            print("form_class: ", form_class)
        if self.kwargs['slug'] == 'transfer':
            print("transfer")
            self.exclude.remove('transfer_to_account')
            form_class = TransactionRecordTransferForm
        # return modelform_factory(self.model, exclude=self.exclude)
        print("form_class: ", form_class)
        return form_class

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_record_type = self.kwargs['slug']
        context['transaction_record_type'] = transaction_record_type
        account_ids = Account.objects.all().values_list('id', 'name')
        credit_card_ids = CreditCard.objects.all().values_list('id', 'name')
        context['account_ids'] = account_ids
        context['creditcard_ids'] = credit_card_ids
        if transaction_record_type == 'expense':
            context['transactionrecord_form'] = 'budgeter/expense_form.html'
        elif transaction_record_type == 'credit_card_payment':
            context['transactionrecord_form'] = 'budgeter/credit_card_payment_form.html'
        elif transaction_record_type == 'deposit':
            context['transactionrecord_form'] = 'budgeter/deposit_form.html'
        elif transaction_record_type == 'withdrawal':
            context['transactionrecord_form'] = 'budgeter/withdrawal_form.html'
        elif transaction_record_type == 'transfer':
            context['transactionrecord_form'] = 'budgeter/transfer_form.html'
        return context

    def form_valid(self, form):
        print("FORM VALID")
        # instance = form.save(commit=False)
        self.instance = self.create_transaction_record()
        print("self.request.POST: ", self.request.POST)
        print("self.request.POST.get('type'): ", self.request.POST.get('type'))
        if self.kwargs['slug'] == 'credit_card_payment':
            account = Account.objects.get(id=self.request.POST.get("account"))
            self.instance.type = 'C'
            self.instance.ledger_type = 'D'
            self.instance.account = None
            self.instance.description = f'Payment from {account.name} to {self.instance.credit_card.name}'
            if not self.request.POST.get('exclude_from_accounting'):
                self.update_credit_card_balance(Decimal(self.request.POST.get('amount')) * int(-1))
                self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)
        if self.kwargs['slug'] == 'expense' and not self.request.POST.get('exclude_from_accounting'):
            if self.request.POST.get('credit_card'):
                self.update_credit_card_balance(Decimal(self.request.POST.get('amount')))
            elif self.request.POST.get('account'):
                self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)
        if self.kwargs['slug'] == 'deposit':
            self.instance.type = 'D'
            self.instance.ledger_type = 'C'
            if not self.request.POST.get('exclude_from_accounting'):
                self.update_account_balance(Decimal(self.request.POST.get('amount')))
        if self.kwargs['slug'] == 'withdrawal':
            self.instance.type = 'W'
            self.instance.ledger_type = 'D'
            if not self.request.POST.get('exclude_from_accounting'):
                self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)
        if self.kwargs['slug'] == 'expense':
            self.instance.type = 'X'
            self.instance.ledger_type = 'D'
        if self.kwargs['slug'] == 'transfer':
            print("***TRANSFER***")
            print("self.request.POST: ", self.request.POST)
            transfer_to_account = Account.objects.get(id=self.request.POST.get('transfer_to_account'))
            self.instance.type = 'T'
            self.instance.ledger_type = 'D'
            self.instance.description = f'Transfer to {transfer_to_account.name}'
            self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)
            transfer_from_instance = self.create_transaction_record()
            transfer_from_instance.account = transfer_to_account
            transfer_from_instance.type = 'T'
            transfer_from_instance.ledger_type = 'C'
            transfer_from_instance.description = f'Transfer from {instance.account.name}'
            transfer_from_instance.save()
            self.update_account_balance(Decimal(self.request.POST.get('amount')), transfer_to_account.id)
            # instance.type = 'X'
            # instance.ledger_type = 'D'

        self.instance.save()
        return super().form_valid(form)

    def create_transaction_record(self):
        new_transaction = TransactionRecord()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        new_transaction.description = self.request.POST.get('description')
        new_transaction.category = self.request.POST.get('category')
        new_transaction.sub_category = self.request.POST.get('sub_category')
        if self.request.POST.get('account'):
            print("self.request.POST.get('account'): ", self.request.POST.get('account'))
            new_transaction.account = Account.objects.get(id=self.request.POST.get('account'))
        if self.request.POST.get('credit_card'):
            print("self.request.POST.get('credit_card'): ", self.request.POST.get('credit_card'))
            new_transaction.credit_card = CreditCard.objects.get(id=self.request.POST.get('credit_card'))
        #add timestamp?
        if not self.request.POST.get('has_expense_items'):
            new_transaction.has_expense_items = False
        else:
            new_transaction.has_expense_items = True
        if not self.request.POST.get('exclude_from_accounting'):
            new_transaction.exclude_from_accounting = False
        else:
            new_transaction.exclude_from_accounting = True
        new_transaction.save()
        print("new_transaction: ", new_transaction)
        return new_transaction

    def update_credit_card_balance(self, amount):
        credit_card = CreditCard.objects.get(id=self.request.POST.get('credit_card'))
        credit_card.balance += amount
        credit_card.save()
        return

    def update_account_balance(self, amount, account_id=None):
        if account_id:
            account = Account.objects.get(id=account_id)
        else:
            account = Account.objects.get(id=self.request.POST.get('account'))
        account.balance += amount
        account.save()
        return

    def form_invalid(self, form):
        print("INVALID")
        print(form.errors)
        return super().form_valid(form)

    def get_success_url(self):
        print("SUCCESS**********")
        if self.request.POST.get('has_expense_items'):
            return reverse('add_expense_item', kwargs = { 'transaction_record_pk': self.instance.id })
        else:
            return reverse('index')

class TransactionRecordsListView(ListView):
    model = TransactionRecord
    # context_object_name = 'transactions'

    def get_transaction_types(self):
        if 'transaction_types' in self.request.GET and self.request.GET['transaction_types'] is not '':
            return self.request.GET.getlist('transaction_types')
        else:
            return ['D', 'W', 'T', 'X', 'AC', 'AD']

    def get_accounts(self):
        if 'accounts' in self.request.GET and self.request.GET['accounts'] is not '':
            print("self.request.GET.get('accounts'): ", self.request.GET.get('accounts'))
            return Account.objects.filter(id__in=self.request.GET.getlist('accounts'))
        else:
            print("NONE")
            return None

    def get_date_range(self):
        if 'start_date' in self.request.GET and self.request.GET['start_date'] is not '':
            start_date = self.request.GET['start_date']
            if self.request.GET['end_date']:
                end_date = self.request.GET['end_date']
            else:
                end_date = datetime.today().strftime('%Y-%m-%d')
            return [start_date, end_date]
        else:
            return ['2021-01-01', datetime.today().strftime('%Y-%m-%d')]

    def get_queryset(self):
        queryset = super().get_queryset()
        date_range = self.get_date_range()
        transaction_types = self.get_transaction_types()
        accounts = self.get_accounts()
        all_accounts = Account.objects.all()
        if accounts is None:
            accounts = all_accounts
        queryset = queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        transaction_types = self.get_transaction_types()

        date_range = self.get_date_range()
        context['start_date'] = date_range[0]
        context['end_date'] = date_range[1]

        accounts = self.get_accounts()
        all_accounts = list(Account.objects.all())
        all_accounts.extend(list(CreditCard.objects.all()))
        if accounts is None:
            accounts = all_accounts
        context['accounts'] = accounts
        context['all_accounts'] = all_accounts
        print("context['accounts']: ", context['accounts'])

        print("date_range: ", date_range)

        # self.object_list = super().get_queryset().filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')

        print("self.object_list: ", self.object_list)

        context['transactions'] = self.object_list
        # context['transactions'] = [self.format_transaction(transaction) for transaction in transactions_list]
        if self.object_list.count() == 0:
            context['transactions_total'] = 0
        else:
            context['transactions_total'] = round(self.object_list.aggregate(Sum('amount'))['amount__sum'], 2)
        context['base_template'] = 'budgeter/base.html'
        return context

class TransactionRecordDetailView(DetailView):
    model = TransactionRecord

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.has_expense_items:
            expense_items = ExpenseItem.objects.filter(transaction_record_id=self.object.id)
            context['expense_items'] = expense_items
        return context

class DeleteTransactionRecordView(DeleteView):
    model = TransactionRecord

    def get_success_url(self):
        self.update_balances()
        return reverse('index')

    def update_balances(self):
        print("self.object.type: ", self.object.type)
        if self.object.type == 'X' or self.object.type == 'W':
            if self.object.account:
                account = Account.objects.get(id=self.object.account.id)
                account.balance += self.object.amount
                account.save()
            if self.object.credit_card:
                credit_card = CreditCard.objects.get(id=self.object.credit_card.id)
                credit_card.balance -= self.object.amount
                credit_card.save()
        elif self.object.type == 'D':
            account = Account.objects.get(id=self.object.account.id)
            account.balance -= self.object.amount
            account.save()
        return

class UpdateTransactionRecordView(FormView):
    model = TransactionRecord
    fields = '__all__'
    template_name = 'budgeter/transactionrecord_form.html'
    success_url = '/budgeter/'

    def get_transaction_record(self):
        return TransactionRecord.objects.get(id=self.kwargs['pk'])

    def get_form_class(self):
        print("get_form_class")
        form_class = super().get_form_class()

        transaction_record = self.get_transaction_record()
        print("transaction_record: ", transaction_record)
        print("transaction_record.type: ", transaction_record.type)

        self.exclude = ['type', 'ledger_type', 'has_expense_items', 'transfer_to_account']
        if transaction_record.type == 'X':
            self.exclude.remove('has_expense_items')
            form_class = TransactionRecordExpenseForm
        elif transaction_record.type == 'C':
            print("CREDIT CARD")
            form_class = TransactionRecordCreditCardPaymentForm
            print("form_class: ", form_class)
        elif transaction_record.type == 'T':
            print("transfer")
            self.exclude.remove('transfer_to_account')
            form_class = TransactionRecordTransferForm
        else:
            form_class = TransactionRecordBaseForm
        # return modelform_factory(self.model, exclude=self.exclude)
        print("form_class: ", form_class)
        return form_class

    def get_initial(self):
        initial = super().get_initial()
        transaction_record = self.get_transaction_record()
        for key, value in model_to_dict(transaction_record).items():
            if key is 'date':
                print(value)
                initial[key] = value
            else:
                initial[key] = value
        print("initial: ", initial)
        return initial

    def get_context_data(self, **kwargs):
        print("UpdateTransactionRecordView****")
        context = super().get_context_data(**kwargs)
        transaction_record = self.get_transaction_record()
        transaction_record_type = '_'.join(transaction_record.get_type_display().lower().split(' '))
        if transaction_record.credit_card:
            context['selected_credit_card'] = transaction_record.credit_card.id
        if transaction_record.account:
            context['selected_account'] = transaction_record.account.id
        context['transaction_record_type'] = transaction_record_type
        print("transaction_record_type: ", transaction_record_type)
        context['transactionrecord_form'] = f'budgeter/{transaction_record_type}_form.html'
        account_ids = Account.objects.all().values_list('id', 'name')
        credit_card_ids = CreditCard.objects.all().values_list('id', 'name')
        context['account_ids'] = account_ids
        context['creditcard_ids'] = credit_card_ids
        print("context: ", context)
        return context

    def form_valid(self, form):
        transaction_record = self.get_transaction_record()
        for key, value in model_to_dict(transaction_record).items():
            print(key, ": ", value)
        if transaction_record.ledger_type == 'C':
            print("CREDIT")
            if self.request.POST.get('account') is not '':
                print("transaction_record.amount: ", transaction_record.amount, "self.request.POST.get('amount'): ", self.request.POST.get('amount'))
                if transaction_record.amount != self.request.POST.get('amount'):
                    self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount) * -1)
                    self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')))
            elif self.request.POST.get('credit_card') is not '':
                if transaction_record.amount != self.request.POST.get('amount'):
                    self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(self.request.POST.get('amount')) - Decimal(transaction_record.amount))

        elif transaction_record.ledger_type == 'D':
            print("DEBIT")
            if self.request.POST.get('account') is not '':
                if transaction_record.amount != self.request.POST.get('amount'):
                    self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
                    self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
            elif self.request.POST.get('credit_card') is not '':
                if transaction_record.amount != self.request.POST.get('amount'):
                    self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(self.request.POST.get('amount')) - Decimal(transaction_record.amount))

        for key, value in self.request.POST.items():
            if key is not 'csrfmiddlewaretoken':
                print("key: ", key, " value: ", value, " value type: ", type(value))
                if key == 'account':
                    print("KEY IS ACCOUNT. VALUE: ", value)
                    if value is not '':
                        print("ACCOUNT")
                        value = Account.objects.get(id=value)
                        setattr(transaction_record, key, value)
                    else:
                        setattr(transaction_record, key, None)
                elif key == 'credit_card':
                    print("KEY IS CREDIT_CARD. VALUE: ", value)
                    if value is not '':
                        print("CREDIT_CARD")
                        value = CreditCard.objects.get(id=value)
                        setattr(transaction_record, key, value)
                    else:
                        setattr(transaction_record, key, None)
                else:
                    setattr(transaction_record, key, value)
                if value == 'on':
                    setattr(transaction_record, key, True)
                elif value == 'off':
                    setattr(transaction_record, key, False)
        transaction_record.save()
        for key, value in model_to_dict(transaction_record).items():
            print(key, ": ", value)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("FORM INVALID")
        return super().form_invalid(form)

    def update_account_balance(self, account_id, difference):
        print("update_account_balance")
        account = Account.objects.get(id=account_id)
        account.balance += difference
        account.save()
        print("account balance: ", account.balance)
        return

    def update_credit_card_balance(self, credit_card_id, difference):
        print("update_credit_card_balance")
        print("difference: ", difference)
        credit_card = CreditCard.objects.get(id=credit_card_id)
        credit_card.balance += difference
        credit_card.save()
        return

    # def get_success_url(self):
    #     return reverse('index')


class ExpenseItemCreateView(CreateView):
    model = ExpenseItem
    # exclude = ['expense']
#
#    def form_valid(self, form):
#        if form.add_new_item:
#            success_url = reverse('add_expense_item', kwargs={'expense_pk': self.object.expense.id})
#            return super().form_valid(form)
#        else:
#            success_url = '/budgeter/'
#            return super().form_valid(form)

    def get_form_class(self):
        self.exclude = ['transaction_record']
        return modelform_factory(self.model, exclude=self.exclude)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['amount'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['note'].widget = forms.TextInput(attrs={'class':'form-control'})
        return form

    def form_valid(self, form):
        instance = form.save(commit=False)
        # form = super().form_valid(form)
        print("instance: ", instance)
        instance.transaction_record = TransactionRecord.objects.get(id=self.kwargs['transaction_record_pk'])
        return super().form_valid(form)

    def get_success_url(self):
        print("Next: ", self.request.POST.get('add_new_item'))
        if self.request.POST.get('add_new_item') is not None:
            return reverse('add_expense_item', kwargs={'transaction_record_pk': self.object.transaction_record.id})
        else:
            return reverse('index')

class ExpenseItemUpdateView(UpdateView):
    model = ExpenseItem
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['update_expense_item'] = True
        return context

    def get_form_class(self):
        self.exclude = ['transaction_record']
        return modelform_factory(self.model, exclude=self.exclude)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['amount'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['note'].widget = forms.TextInput(attrs={'class':'form-control'})
        return form

    def get_success_url(self):
        return reverse('transaction_record_detail_view', kwargs={ 'pk': self.object.transaction_record.id })

class ExpenseItemDeleteView(DeleteView):
    model = ExpenseItem

    def get_success_url(self):
        return reverse('transaction_record_detail_view', kwargs={ 'pk': self.object.transaction_record.id })


class ExpenseItemListView(ListView):
    model = ExpenseItem
    context_object_name = 'expense_items'

    def get_expense_items(self):
        if 'pk' in self.kwargs:
            return super().get_queryset().filter(expense_id=self.kwargs['pk'])
        else:
            return super().get_queryset().all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        # context['transactions'] = transactions_list
        context['expense_items_list'] = self.get_expense_items()
        # context['transaction_data'] = self.format_transaction(transaction)
        # context['transactions_total'] = round(transactions_list.aggregate(Sum('amount'))['amount__sum'], 2)
        # print("transaction_data: ", context['transaction_data'])
        return context

    def format_transaction(self, transaction):
        if transaction.type is 'X':
            return { "transaction": transaction, "transaction_type": Expense.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'D':
            return { "transaction": transaction, "transaction_type": Deposit.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'W':
            return { "transaction": transaction, "transaction_type": Withdrawal.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'T':
            return { "transaction": transaction, "transaction_type": Transfer.objects.get(transaction_id=transaction.id) }
        else:
            return { "transaction": transaction, "transaction_type": Adjustment.objects.get(transaction_id=transaction.id) }



class AddTransactionView(TemplateView):
    template_name = 'budgeter/add_transaction.html'

class TransactionListView(ListView):
    model = Transaction
    context_object_name = 'transactions'

    def get_transaction_types(self):
        if 'transaction_types' in self.request.GET and self.request.GET['transaction_types'] is not '':
            return self.request.GET.getlist('transaction_types')
        else:
            return ['D', 'W', 'T', 'X', 'AC', 'AD']

    def get_accounts(self):
        if 'accounts' in self.request.GET and self.request.GET['accounts'] is not '':
            print("self.request.GET.get('accounts'): ", self.request.GET.get('accounts'))
            return Account.objects.filter(id__in=self.request.GET.getlist('accounts'))
        else:
            print("NONE")
            return None

    def get_date_range(self):
        if 'start_date' in self.request.GET and self.request.GET['start_date'] is not '':
            start_date = self.request.GET['start_date']
            if self.request.GET['end_date']:
                end_date = self.request.GET['end_date']
            else:
                end_date = datetime.today().strftime('%Y-%m-%d')
            return [start_date, end_date]
        else:
            return ['2021-01-01', datetime.today().strftime('%Y-%m-%d')]

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        transaction_types = self.get_transaction_types()

        date_range = self.get_date_range()
        context['start_date'] = date_range[0]
        context['end_date'] = date_range[1]

        accounts = self.get_accounts()
        all_accounts = Account.objects.all()
        if accounts is None:
            accounts = all_accounts
        context['accounts'] = accounts
        context['all_accounts'] = all_accounts
        print("context['accounts']: ", context['accounts'])

        transactions_list = super().get_queryset().filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
        # context['transactions'] = transactions_list
        context['transactions'] = [self.format_transaction(transaction) for transaction in transactions_list]
        context['transactions_total'] = round(transactions_list.aggregate(Sum('amount'))['amount__sum'], 2)
        context['base_template'] = 'budgeter/base.html'
        return context

    def format_transaction(self, transaction):
        print("transaction.id: ", transaction.id)
        if transaction.type is 'X':
            return { "transaction": transaction, "transaction_type": Expense.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'D':
            return { "transaction": transaction, "transaction_type": Deposit.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'W':
            return { "transaction": transaction, "transaction_type": Withdrawal.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'T':
            return { "transaction": transaction, "transaction_type": Transfer.objects.get(transaction_id=transaction.id) }
        else:
            return { "transaction": transaction, "transaction_type": Adjustment.objects.get(transaction_id=transaction.id) }

class TransactionDetailView(DetailView):
    model = Transaction
    context_object_name = 'transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        transactions_list = super().get_queryset().order_by('-date')
        # context['transactions'] = transactions_list
        transaction = self.get_object()
        print("transaction: ", transaction)
        context['transaction_data'] = self.format_transaction(transaction)
        context['transactions_total'] = round(transactions_list.aggregate(Sum('amount'))['amount__sum'], 2)
        print("transaction_data: ", context['transaction_data'])
        return context

    def format_transaction(self, transaction):
        if transaction.type is 'X':
            return { "transaction": transaction, "transaction_type": Expense.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'D':
            return { "transaction": transaction, "transaction_type": Deposit.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'W':
            return { "transaction": transaction, "transaction_type": Withdrawal.objects.get(transaction_id=transaction.id) }
        elif transaction.type is 'T':
            return { "transaction": transaction, "transaction_type": Transfer.objects.get(transaction_id=transaction.id) }
        else:
            return { "transaction": transaction, "transaction_type": Adjustment.objects.get(transaction_id=transaction.id) }


class TransactionUpdateView(UpdateView):
    model = Transaction
    fields = '__all__'

    def get_object(self, **kwargs):
        # context = super().get_context_data()
        transaction_qs = super().get_queryset()
        # context['transactions'] = transactions_list
        transaction = super().get_object(queryset=transaction_qs)
        print("transaction: ", transaction)
        # context['transaction_data'] = self.format_transaction(transaction)
        # context['transactions_total'] = round(transactions_list.aggregate(Sum('amount'))['amount__sum'], 2)
        # print("transaction_data: ", context['transaction_data'])

        print("transaction.id: ", transaction.id)

        if transaction.type is 'X':
            print("EXPENSE")
            item = Expense.objects.get(transaction_id=transaction.id)
            print("ITEM: ", item)
            return item
        elif transaction.type is 'D':
            print("DEPOSIT")
            item = Deposit.objects.get(transaction_id=transaction.id)
            print("ITEM: ", item)
            return item
        elif transaction.type is 'W':
            print("WITHDRAWAL")
            item = Withdrawal.objects.get(transaction_id=transaction.id)
            print("item: ", item)
            return item
        elif transaction.type is 'T':
            print("TRANSFER")
            return Transfer.objects.get(transaction_id=transaction.id)
        else:
            print("ADJUSTMENT")
            return Adjustment.objects.get(transaction_id=transaction.id)


        # return context

    # def format_transaction(self, transaction):
    #     if transaction.type is 'X':
    #         return { "transaction": transaction, "transaction_type": Expense.objects.get(transaction_id=transaction.id) }
    #     elif transaction.type is 'D':
    #         return { "transaction": transaction, "transaction_type": Deposit.objects.get(transaction_id=transaction.id) }
    #     elif transaction.type is 'W':
    #         return { "transaction": transaction, "transaction_type": Withdrawal.objects.get(transaction_id=transaction.id) }
    #     elif transaction.type is 'T':
    #         return { "transaction": transaction, "transaction_type": Transfer.objects.get(transaction_id=transaction.id) }
    #     else:
    #         return { "transaction": transaction, "transaction_type": Adjustment.objects.get(transaction_id=transaction.id) }


class DeleteMultipleModelsMixin:
    def delete_related_objects(self, transaction, **kwargs):
        # transaction = kwargs['transaction']
        if transaction.type is 'X':
            expense = Expense.objects.get(transaction_id=transaction.id)
            if expense.has_expense_items:
                expense_items = ExpenseItem.objects.filter(expense_id=expense.id)
                expense_items.delete()
            expense.delete()
        elif transaction.type is 'D':
            deposit = Deposit.objects.get(transaction_id=transaction.id)
            deposit.delete()
        elif transaction.type is 'W':
            withdrawal = Withdrawal.objects.get(transaction_id=transaction.id)
            withdrawal.delete()
        elif transaction.type is 'T':
            transfer = Transfer.objects.get(transaction_id=transaction.id)
            transfer.delete()
        else:
            adjustment = Adjustment.objects.get(transaction_id=transaction.id)
            adjustment.delete()
        return kwargs

class TransactionDeleteView(DeleteView, DeleteMultipleModelsMixin):
    model = Transaction
    context_object_name = 'transaction'

    def get_success_url(self):
        return reverse('expense_detail_view', kwargs={ "pk": self.request.POST.get('pk') })

    def delete_related_objects(self, transaction, **kwargs):
        super().delete_related_objects(kwargs)
        return reverse('index')


class AddDepositView(CreateView):
    model = Deposit
    fields = ['date', 'amount', 'to_account', 'note']

    def form_valid(self, form):
        new_transaction = self.create_transaction()
        form.instance.transaction = new_transaction
        return super(AddDepositView, self).form_valid(form)

    def get_success_url(self):
        self.update_account_balance()
        return reverse('index')

    def update_account_balance(self):
        account = Account.objects.get(id=self.request.POST.get('to_account'))
        account.balance = account.balance + Decimal(self.request.POST.get('amount'))
        account.save()
        return

    def create_transaction(self):
        new_transaction = Transaction()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        new_transaction.type = "D"
        new_transaction.ledger_type = 'C'
        account = Account.objects.all()
        new_transaction.account = Account.objects.get(id=self.request.POST.get('to_account'))
        new_transaction.save()
        return new_transaction

class AddWithdrawalView(CreateView):
    model = Withdrawal
    fields = ['date', 'amount', 'from_account', 'note']

    def form_valid(self, form):
        new_transaction = self.create_transaction()
        form.instance.transaction = new_transaction
        return super(AddWithdrawalView, self).form_valid(form)

    def get_success_url(self):
        self.update_account_balance()
        return reverse('index')

    def update_account_balance(self):
        account = Account.objects.get(id=self.request.POST.get('from_account'))
        account.balance = account.balance - Decimal(self.request.POST.get('amount'))
        account.save()
        return

    def create_transaction(self):
        new_transaction = Transaction()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        new_transaction.type = "W"
        new_transaction.ledger_type = 'D'
        account = Account.objects.all()
        new_transaction.account = Account.objects.get(id=self.request.POST.get('from_account'))
        new_transaction.save()
        return new_transaction

class AddTransfer(CreateView):
    model = Transfer
    fields = ['date', 'amount', 'from_account', 'to_account', 'note']

    def form_valid(self, form):
        new_transaction = self.create_transaction()
        form.instance.transaction = new_transaction
        return super(AddTransfer, self).form_valid(form)

    def get_success_url(self):
        self.update_account_balances()
        return reverse('index')

    def update_account_balances(self):
        from_account = Account.objects.get(id=self.request.POST.get('from_account'))
        to_account = Account.objects.get(id=self.request.POST.get('to_account'))
        from_account.balance = from_account.balance - Decimal(self.request.POST.get('amount'))
        to_account.balance = to_account.balance + Decimal(self.request.POST.get('amount'))
        from_account.save()
        to_account.save()
        return

    def create_transaction(self):
        new_transaction = Transaction()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        new_transaction.type = "T"
        new_transaction.ledger_type = 'Z'
        new_transaction.save()
        return new_transaction

class AddAdjustmentView(CreateView):
    model = Adjustment
    fields = ['date', 'type', 'amount', 'account', 'note']

    def form_valid(self, form):
        new_transaction = self.create_transaction(self.update_account_balance())
        form.instance.transaction = new_transaction
        return super(AddAdjustmentView, self).form_valid(form)

    def get_success_url(self):
        return reverse('index')

    def update_account_balance(self):
        account = Account.objects.get(id=self.request.POST.get('account'))
        if self.request.POST.get('type') is 'D':
            amount = Decimal(self.request.POST.get('amount')) * -1
            transaction_type = 'AD'
        else:
            amount = Decimal(self.request.POST.get('amount'))
            transaction_type = 'AC'
        account.balance = account.balance + amount
        account.save()
        return transaction_type

    def create_transaction(self, transaction_type):
        new_transaction = Transaction()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        new_transaction.type = transaction_type
        if transaction_type is 'AC':
            form.instance.ledger_type = 'C'
        elif transaction_type is 'AD':
            form.instance.ledger_type = 'D'
        else:
            form.instance.ledger_type = 'Z'
        account = Account.objects.all()
        new_transaction.account = Account.objects.get(id=self.request.POST.get('account'))
        new_transaction.save()
        return new_transaction

# class MarkAsPaid(View):
#     def dispatch(self):
#         create_expense(self.request.POST.get('expense_id'))
#         return super().dispatch(*args, **kwargs)
#     def get_expense_data(self, expense_id):
#         return RecurringExpense.objects.filter(id=expense_id)
#
#     def create_transaction(self):
#         new_transaction = Transaction()
#         new_transaction.date = self.request.POST.get('date')
#         new_transaction.amount = self.request.POST.get('amount')
#         new_transaction.type = 'X'
#         new_transaction.ledger_type = 'D'
#         account = Account.objects.all()
#         new_transaction.account = Account.objects.get(id=self.request.POST.get('from_account'))
#         new_transaction.save()
#         return new_transaction
#
#     def create_expense(self):
#         expense_data = self.get_expense_data()
#         new_transaction = self.create_transaction()
#         new_expense = Expense()
#         new_expense.amount = expense_data.amount
#         new_expense.date = expense_data
#         new_expense.from_account = expense_data
#         new_expense.paid_to = expense_data.paid_to
#         new_expense.note = expense_data.note
#         new_expense.transaction = new_transaction
#         new_expense.category = expense_data.category
#         new_expense.recurring_expense = expense_data
#         new_expense.save()
#         return

class CreateExpenseView(CreateView):
    model = Expense
    fields = ['paid_to', 'amount', 'date', 'debit_from_account', 'from_account', 'category', 'note', 'has_expense_items']
    # form_class = ExpenseForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
    #     FROM_ACCOUNT_CHOICES = [("N", "None"), ("C", "Cash"),]
    #     accounts = Account.objects.all() #need to use the user_id after auth is implemented
    #     FROM_ACCOUNT_CHOICES.extend([(account.id, account.name) for account in accounts])
    #     form.fields['from_account'].choices = FROM_ACCOUNT_CHOICES
        return form
    #
    def form_valid(self, form):
        print("VALID")
        new_transaction = self.create_transaction()
        form.instance.transaction = new_transaction
        return super(CreateExpenseView, self).form_valid(form)
    #
    def form_invalid(self, form):
        print("INVALID")
        return super(CreateExpenseView, self).form_invalid(form)

    def get_success_url(self):
        if self.request.POST.get('from_account'):
            self.update_account_balance()
        if self.request.POST.get('has_expense_items') is not None:
            return reverse('add_expense_item', kwargs={'expense_pk': self.object.id})
        else:
            return reverse('index')

    def update_account_balance(self):
        account = Account.objects.get(id=self.request.POST.get('from_account'))
        print("Account Balance: ", account.balance)
        print("Amount: ", Decimal(self.request.POST.get('amount')))
        account.balance = account.balance - Decimal(self.request.POST.get('amount'))
        print("Account Balance: ", account.balance)
        account.save()
        return

    def create_transaction(self):
        new_transaction = Transaction()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        new_transaction.type = 'X'
        new_transaction.ledger_type = 'D'
        account = Account.objects.all()
        if self.request.POST.get('from_account'):
            new_transaction.account = Account.objects.get(id=self.request.POST.get('from_account'))
        new_transaction.save()
        return new_transaction

class CreateRecurringExpenseView(CreateView):
    model = RecurringExpense
    fields = ['payment_due_date_day', 'amount', 'paid_to', 'category', 'note']

    def get_success_url(self):
        # self.create_recurring_expense()
        return reverse('index')

    # def create_recurring_expense(self):
    #     new_recurring_expense = RecurringExpense()
    #     new_recurring_expense.payment_due_date_day = self.request.POST.get('payment_due_date_day')
    #     new_recurring_expense.amount = self.request.POST.get('amount')
    #     new_recurring_expense.paid_to = self.request.POST.get('paid_to')
    #     new_recurring_expense.note = self.request.POST.get('note')
    #     new_recurring_expense.category = self.request.POST.get('category')
    #     new_recurring_expense.save()
    #     return

class ExpenseListView(ListView):
    model = Expense
    context_object_name = 'expenses'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['base_template'] = 'budgeter/base.html'

        date_range = self.get_date_range()
        print("date_range: ", date_range)
        context['start_date'] = date_range[0]
        context['end_date'] = date_range[1]

        accounts = self.get_accounts()
        all_accounts = Account.objects.all()
        if accounts is None:
            accounts = all_accounts
        context['accounts'] = accounts
        context['all_accounts'] = all_accounts

        payees = self.get_payees()
        all_payees = super().get_queryset().values_list('paid_to', flat=True).distinct()
        if payees is None:
            payees = all_payees
        context['payees'] = payees
        context['all_payees'] = all_payees
        print("context['all_payees']: ", context['all_payees'], ", context['payees']: ", context['payees'])

        context['expenses'] = Expense.objects.filter(from_account__in=accounts, date__gte=date_range[0], date__lte=date_range[1], paid_to__in=payees)

        return context

    def get_accounts(self):
        if 'accounts' in self.request.GET and self.request.GET['accounts'] is not '':
            print("self.request.GET.get('accounts'): ", self.request.GET.get('accounts'))
            return Account.objects.filter(id__in=self.request.GET.getlist('accounts'))
        else:
            print("NONE")
            return None

    def get_payees(self, **kwargs):
        if 'payees' in self.request.GET and self.request.GET['payees'] is not '':
            return self.request.GET.getlist('payees')
        else:
            return super().get_queryset().values_list('paid_to', flat=True).distinct()

    def get_date_range(self):
        if 'start_date' in self.request.GET and self.request.GET['start_date'] is not '':
            start_date = self.request.GET['start_date']
            if self.request.GET['end_date']:
                end_date = self.request.GET['end_date']
            else:
                end_date = datetime.today().strftime('%Y-%m-%d')
            return [start_date, end_date]
        else:
            return ['2021-01-01', datetime.today().strftime('%Y-%m-%d')]

class ExpenseDetailView(DetailView):
    model = Expense

class ExpenseDeleteView(DeleteView):
    model = Expense

    def get_success_url(self):
        return reverse('expense_detail_view', kwargs={ "pk": self.request.POST.get('pk') })

class ExpenseUpdateView(UpdateView):
    model = Expense
    fields = ['amount', 'date', 'from_account', 'paid_to', 'note', 'has_expense_items']

    def get_success_url(self):
        self.update_account_balance()
        print("pk", self.request.POST.get('pk'))
        return reverse('expense_detail_view', kwargs={ "pk": self.request.POST.get('pk') })

    def get_initial(self):
        initial_values = super().get_initial()
        return initial_values

    def form_valid(self, form):
        self.update_account_balance()
        return super().form_valid(form)

    def update_account_balance(self):
        account = Account.objects.get(id=self.request.POST.get('from_account'))
        current_amount = Expense.objects.get(id=self.object.id).amount
        self.get_initial()
        difference = Decimal(self.request.POST.get('amount')) - current_amount
        account.balance = account.balance - difference
        account.save()
        return
