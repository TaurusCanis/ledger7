from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse, resolve
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from budgeter.models import Account, Expense, ExpenseItem, Deposit, Withdrawal, Adjustment, Transfer, Transaction, TransactionRecord, RecurringExpense, CreditCard, TransferAccounts, Category, SubCategory, Description, CreditCardPayment
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime
from django import forms
from budgeter.forms import TransactionRecordBaseForm, TransactionRecordExpenseForm, TransactionRecordTransferForm, TransactionRecordCreditCardPaymentForm, TransactionRecordAdjustmentForm
from django.forms import modelform_factory
from django.forms.models import model_to_dict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login


class IndexView(TemplateView):
    template_name = 'budgeter/index.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'budgeter/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        accounts = Account.objects.filter(user=self.request.user)
        # transactions_list = Transaction.objects.filter(user=self.request.user).order_by('-date')
        # last_five_transactions = Transaction.objects.all().order_by('-date')[:5]
        # context['transactions'] = last_five_transactions

        transaction_records_list = TransactionRecord.objects.filter(user=self.request.user).order_by('-date')[:10]
        # if transaction_records_list.count() != 0:
        #     print("transaction_records_list[0].amount: ", transaction_records_list[0].amount)
        #     print("transactions_list.aggregate(Sum('amount'))['amount__sum']: ", transactions_list.aggregate(Sum('amount'))['amount__sum'])
        context['transaction_records_list'] = transaction_records_list

        credit_cards = CreditCard.objects.filter(user=self.request.user)
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

class UserCreationView(CreateView):
    print("CREATION VIEW")
    form_class = UserCreationForm
    template_name = 'auth/user_form.html'

    def get_success_url(self):
        user = authenticate(username=self.request.POST.get('username'), password=self.request.POST.get('password1'))
        if user is not None:
            print("AUTHETICATED")
            login(self.request, user)
            return reverse('dashboard', kwargs={ 'pk': user.id })

        else:
            print("NOT AUTHENTICATED")
            return redirect('register')


class LoginView(LoginView):
    print("LOGIN VIEW")
    def get_success_url(self):
        print("LOGGED IN!")
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class LogoutView(LogoutView):
    next_page = 'index'
    print("LOGOUT VIEW")
    def get_success_url(self):
        print("LOGGED OUT")
        return reverse('index')

class CreateAccountView(LoginRequiredMixin, CreateView):
    model = Account
    fields = ['name', 'balance', 'type', 'exclude_from_available_funds']

    def form_valid(self, form):
        account = form.save(commit=False)
        account.user_id = self.request.user.id
        account.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = Account
    fields = ['name', 'balance', 'type', 'exclude_from_available_funds']

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['balance'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['type'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['exclude_from_available_funds'].widget = forms.CheckboxInput(attrs={'class':'form-check-input'})
        return form

class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['total_available_funds'] = round(super().get_queryset().aggregate(Sum('balance'))['balance__sum'], 2)
        context['standalone'] = True
        context['base_template'] = 'budgeter/base.html'
        return context

class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     print("self.object.id: ", self.object.id)
    #     transaction_records_list = TransactionRecord.objects.filter(account=self.object.id).order_by('date')
    #     print("transaction_records_list: ", transaction_records_list)
    #     context['transaction_records_list'] = transaction_records_list
    #     if transaction_records_list.count() == 0:
    #         context['transaction_records_total'] = 0
    #     else:
    #         context['transaction_records_total'] = round(transaction_records_list.aggregate(Sum('amount'))['amount__sum'], 2)
    #     context['base_template'] = 'budgeter/no_base.html'
    #     return context

    def get_transaction_types(self):
        if 'transaction_types' in self.request.GET and self.request.GET['transaction_types'] is not '':
            return self.request.GET.getlist('transaction_types')
        else:
            return ['D', 'W', 'T', 'X', 'AC', 'AD']

    def get_accounts(self):
        print("self.request.GET: ", self.request.GET)
        if 'accounts' in self.request.GET and self.request.GET['accounts'] is not '':
            print("self.request.GET.get('accounts'): ", self.request.GET.get('accounts'))
            return Account.objects.filter(id__in=self.request.GET.getlist('accounts'), user=self.request.user)
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

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     date_range = self.get_date_range()
    #     transaction_types = self.get_transaction_types()
    #     accounts = self.get_accounts()
    #     all_accounts = Account.objects.all()
    #     if accounts is None:
    #         accounts = all_accounts
    #     queryset = queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
    #     return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        if 'account_id' in self.kwargs:
            print("IN")
            context['account_id'] = self.kwargs['account_id']
            print("self.kwargs['account_id']: ", self.kwargs['account_id'])
        elif 'pk' in self.kwargs:
            print("PK")
            context['account_id'] = self.kwargs['pk']
            print("self.kwargs['account_id']: ", self.kwargs['pk'])
        else:
            print("OUT")
            context['account_id'] = None
        print("context: ", context)

        transactionrecord_queryset = TransactionRecord.objects.filter(account=self.object)
        date_range = self.get_date_range()
        transaction_types = self.get_transaction_types()
        accounts = self.get_accounts()
        all_accounts = Account.objects.filter(user=self.request.user)
        if accounts is None:
            accounts = all_accounts
        transaction_record_list = transactionrecord_queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
        context['transaction_record_list'] = transaction_record_list

        transaction_types = self.get_transaction_types()

        date_range = self.get_date_range()
        context['start_date'] = date_range[0]
        context['end_date'] = date_range[1]

        accounts = self.get_accounts()
        all_accounts = list(Account.objects.filter(user=self.request.user))
        all_accounts.extend(list(CreditCard.objects.filter(user=self.request.user)))
        if accounts is None:
            accounts = all_accounts
        context['accounts'] = accounts
        context['all_accounts'] = all_accounts
        print("context['accounts']: ", context['accounts'])

        print("date_range: ", date_range)

        # self.object_list = super().get_queryset().filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')

        context['next_url'] = 'account_detail'

        context['transactions'] = transaction_record_list
        # context['transactions'] = [self.format_transaction(transaction) for transaction in transactions_list]
        if transaction_record_list.count() == 0:
            context['transactions_total'] = 0
        else:
            context['transactions_total'] = round(transaction_record_list.aggregate(Sum('amount'))['amount__sum'], 2)
        context['base_template'] = 'budgeter/no_base.html'
        return context

class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = Account

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class CreateCreditCardView(LoginRequiredMixin, CreateView):
    model = CreditCard
    fields = ['name', 'balance', 'interest_rate']

    def form_valid(self, form):
        credit_card = form.save(commit=False)
        credit_card.user_id = self.request.user.id
        credit_card.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class UpdateCreditCardView(LoginRequiredMixin, UpdateView):
    model = CreditCard
    fields = ['name', 'balance', 'interest_rate']

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['balance'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['interest_rate'].widget = forms.TextInput(attrs={'class':'form-control'})
        return form

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class DeleteCreditCardView(LoginRequiredMixin, DeleteView):
    model = CreditCard

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class CreditCardDetailView(LoginRequiredMixin, DetailView):
    model = CreditCard

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['base_template'] = 'budgeter/no_base.html'
    #     transaction_records_list = TransactionRecord.objects.filter(credit_card=self.object.id).order_by('date')
    #     for tr in transaction_records_list:
    #         for k, v in model_to_dict(tr).items():
    #             print("k: ", k, "v: ", v)
    #         print("*********************")
    #     context['transaction_records_list'] = transaction_records_list
    #     if transaction_records_list.count() == 0:
    #         context['transaction_records_total'] = 0
    #     else:
    #         context['transaction_records_total'] = round(transaction_records_list.aggregate(Sum('amount'))['amount__sum'], 2)
    #
    #     return context

    def get_transaction_types(self):
        if 'transaction_types' in self.request.GET and self.request.GET['transaction_types'] is not '':
            return self.request.GET.getlist('transaction_types')
        else:
            return ['D', 'W', 'T', 'X', 'AC', 'AD']

    def get_accounts(self):
        if 'accounts' in self.request.GET and self.request.GET['accounts'] is not '':
            print("self.request.GET.get('accounts'): ", self.request.GET.get('accounts'))
            return Account.objects.filter(user=self.request.user, id__in=self.request.GET.getlist('accounts'))
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

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     date_range = self.get_date_range()
    #     transaction_types = self.get_transaction_types()
    #     accounts = self.get_accounts()
    #     all_accounts = Account.objects.all()
    #     if accounts is None:
    #         accounts = all_accounts
    #     queryset = queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
    #     return queryset

    def get_context_data(self, **kwargs):
        print("HIYA")
        context = super().get_context_data()

        if 'account_id' in kwargs:
            context['account_id'] = kwargs['account_id']
        else:
            context['account_id'] = self.object.id

        transactionrecord_queryset = TransactionRecord.objects.filter(credit_card_id=self.object.id)
        date_range = self.get_date_range()
        transaction_types = self.get_transaction_types()
        accounts = self.get_accounts()
        all_accounts = CreditCard.objects.filter(user=self.request.user)
        if accounts is None:
            accounts = all_accounts
        transaction_record_list = transactionrecord_queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, credit_card__in=all_accounts).order_by('-date')
        context['transaction_record_list'] = transaction_record_list

        transaction_types = self.get_transaction_types()

        date_range = self.get_date_range()
        context['start_date'] = date_range[0]
        context['end_date'] = date_range[1]

        accounts = self.get_accounts()
        all_accounts = list(Account.objects.filter(user=self.request.user))
        all_accounts.extend(list(CreditCard.objects.filter(user=self.request.user)))
        if accounts is None:
            accounts = all_accounts
        context['accounts'] = accounts
        context['all_accounts'] = all_accounts
        print("context['accounts']: ", context['accounts'])

        print("date_range: ", date_range)

        # self.object_list = super().get_queryset().filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')

        context['next_url'] = 'credit_card_detail_view'
        context['account_type'] = 'credit_card'

        context['transactions'] = transaction_record_list
        # context['transactions'] = [self.format_transaction(transaction) for transaction in transactions_list]
        if transaction_record_list.count() == 0:
            context['transactions_total'] = 0
        else:
            context['transactions_total'] = round(transaction_record_list.aggregate(Sum('amount'))['amount__sum'], 2)
        context['base_template'] = 'budgeter/no_base.html'
        return context


class CreditCardListView(LoginRequiredMixin, ListView):
    model = CreditCard

class TransactionRecordOptions(LoginRequiredMixin, TemplateView):
    template_name = 'budgeter/transaction_record_options.html'

## Should probably create separate views for each TransactionRecord Form

class CreateTransactionRecord(LoginRequiredMixin, FormView):
    template_name = 'budgeter/transactionrecord_form.html'
    form_class = TransactionRecordBaseForm

    # model = TransactionRecord
    # exclude = None

    def get_form(self, form_class=None):
        print("kwargs['slug']: ", self.kwargs['slug'])
        form = super().get_form(form_class)
        form.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
        print("Account.objects.values_list('id', 'name'): ", list(Account.objects.filter(user=self.request.user).values_list('id', 'name')))



        # if self.kwargs['slug'] == 'transfer':
        #     form.fields['transfer_to_account'].widget = forms.CharField()
        print("form.fields: ", form.fields)

        credit_card_choice_list = [
            ('', ''),
        ]
        credit_card_choice_list.extend(list(CreditCard.objects.filter(user=self.request.user).values_list('id', 'name')))

        account_choice_list = [
            ('', ''),
        ]
        account_choice_list.extend(list(Account.objects.filter(user=self.request.user).values_list('id', 'name')))

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
        # if self.kwargs['slug'] == 'adjustment':
        #     print("adjustment")
        #     self.exclude.remove('transfer_to_account')
        #     form_class = TransactionRecordAdjustmentForm
        # return modelform_factory(self.model, exclude=self.exclude)
        print("form_class: ", form_class)
        return form_class

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction_record_type = self.kwargs['slug']
        context['transaction_record_type'] = transaction_record_type
        account_ids = Account.objects.filter(user=self.request.user).values_list('id', 'name')
        credit_card_ids = CreditCard.objects.filter(user=self.request.user).values_list('id', 'name')
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
        elif transaction_record_type == 'adjustment':
            context['transactionrecord_form'] = 'budgeter/adjustment_form.html'
        return context

    def form_valid(self, form):
        print("FORM VALID")
        # instance = form.save(commit=False)
        self.instance = self.create_transaction_record()
        print("self.request.POST: ", self.request.POST)
        print("self.request.POST.get('type'): ", self.request.POST.get('type'))
        # if self.kwargs['slug'] == 'credit_card_payment':
            # account = Account.objects.get(id=self.request.POST.get("account"))
            # self.instance.type = 'C'
            # self.instance.ledger_type = 'D'
            # self.instance.description = f'Payment from {account.name} to {self.instance.credit_card.name}'
            # if not self.request.POST.get('exclude_from_accounting'):
            #     self.update_credit_card_balance(Decimal(self.request.POST.get('amount')) * int(-1))
            #     self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)
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
        if self.kwargs['slug'] == 'transfer' or self.kwargs['slug'] == 'credit_card_payment':
            self.instance.ledger_type = 'D'
            account_paid_to = self.create_transaction_record()
            account_paid_to.ledger_type = 'C'
            if self.kwargs['slug'] == 'credit_card_payment':
                print("self.request.POST: ", self.request.POST)
                account = Account.objects.get(id=self.request.POST.get("account"))
                credit_card = CreditCard.objects.get(id=self.request.POST.get("credit_card"))
                self.instance.type = 'C'
                self.instance.credit_card = None
                self.instance.description = Description.objects.get_or_create(user=self.request.user, name=f'Payment to {account.name}')[0]
                account_paid_to.account = account
                account_paid_to.type = 'C'
                account_paid_to.account = None
                account_paid_to.description = Description.objects.get_or_create(user=self.request.user, name=f'Payment from {credit_card.name}')[0]
                account_paid_to.save()
                credit_card_payment = CreditCardPayment()
                credit_card_payment.account = self.instance
                credit_card_payment.credit_card = account_paid_to
                credit_card_payment.user = self.request.user
                credit_card_payment.save()
                print("account_paid_to: ", account_paid_to)
                print("account_paid_to.credit_card: ", account_paid_to.credit_card)
                print("account_paid_to.account: ", account_paid_to.account)
                # self.update_account_balance(Decimal(self.request.POST.get('amount')), account_paid_to.account.id)

                if not self.request.POST.get('exclude_from_accounting'):
                    self.update_credit_card_balance(Decimal(self.request.POST.get('amount')) * int(-1))
                    self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)

            if self.kwargs['slug'] == 'transfer':
                transfer_to_account = Account.objects.get(user=self.request.user, id=self.request.POST.get('transfer_to_account'))
                self.instance.type = 'T'
                self.instance.description = Description.objects.get_or_create(user=self.request.user, name=f'Transfer to {transfer_to_account.name}')[0]
                self.update_account_balance(Decimal(self.request.POST.get('amount')) * -1)
                account_paid_to.account = transfer_to_account
                account_paid_to.type = 'T'
                account_paid_to.description = Description.objects.get_or_create(user=self.request.user, name=f'Transfer from {self.instance.account.name}')[0]
                account_paid_to.save()
                transfer_accounts = TransferAccounts()
                transfer_accounts.account_to = self.instance
                transfer_accounts.account_from = account_paid_to
                transfer_accounts.save()
                self.update_account_balance(Decimal(self.request.POST.get('amount')), transfer_to_account.id)





            # instance.type = 'X'
            # instance.ledger_type = 'D'

        self.instance.save()
        return super().form_valid(form)

    def create_transaction_record(self):
        print("self.request.POST: ", self.request.POST.get('description'))
        print("self.request.POST.get('description') == None: ", self.request.POST.get('description') == None)
        new_transaction = TransactionRecord()
        new_transaction.date = self.request.POST.get('date')
        new_transaction.amount = self.request.POST.get('amount')
        if 'description' in self.request.POST and self.request.POST.get('description') != '':
            new_transaction.description = Description.objects.get_or_create(user=self.request.user, name=self.request.POST.get('description'))[0]
        if 'category' in self.request.POST and self.request.POST.get('category') != '':
            new_transaction.category = Category.objects.get_or_create(user=self.request.user, name=self.request.POST.get('category'))[0]
        if 'sub_category' in self.request.POST and self.request.POST.get('sub_category') != '':
            new_transaction.sub_category = SubCategory.objects.get_or_create(user=self.request.user, name=self.request.POST.get('sub_category'))[0]
        if self.request.POST.get('account'):
            print("self.request.POST.get('account'): ", self.request.POST.get('account'))
            new_transaction.account = Account.objects.get(user=self.request.user, id=self.request.POST.get('account'))
        if self.request.POST.get('credit_card'):
            print("self.request.POST.get('credit_card'): ", self.request.POST.get('credit_card'))
            new_transaction.credit_card = CreditCard.objects.get(user=self.request.user, id=self.request.POST.get('credit_card'))
        #add timestamp?
        if not self.request.POST.get('has_expense_items'):
            new_transaction.has_expense_items = False
        else:
            new_transaction.has_expense_items = True
        if not self.request.POST.get('exclude_from_accounting'):
            new_transaction.exclude_from_accounting = False
        else:
            new_transaction.exclude_from_accounting = True
        new_transaction.user = self.request.user
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
            account = Account.objects.get(user=self.request.user, id=account_id)
        else:
            account = Account.objects.get(user=self.request.user, id=self.request.POST.get('account'))
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
            return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class TransactionRecordsListView(LoginRequiredMixin, ListView):
    model = TransactionRecord
    context_object_name = 'transaction_record_list'

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
        current_url = resolve(self.request.path_info).url_name
        print("account_type: ", self.request.POST.get('account_type'))
        print("self.kwargs: ", self.kwargs)
        queryset = super().get_queryset()
        date_range = self.get_date_range()
        transaction_types = self.get_transaction_types()
        print("transaction_types: ", transaction_types)
        accounts = self.get_accounts()

        if "account_id" in self.kwargs and self.kwargs['account_id'] != 'None':
            print("account_id: ", self.kwargs['account_id'])
            accounts = Account.objects.filter(id=self.kwargs['account_id'])
            all_accounts = Account.objects.all()
            if accounts is None:
                accounts = all_accounts
            queryset = queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
        elif 'account_type' in  self.kwargs and self.kwargs['account_type'] == 'credit_card':
            accounts = CreditCard.objects.all()
            queryset = queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, credit_card__in=accounts).order_by('-date')
        elif 'account_type' in  self.kwargs and self.kwargs['account_type'] == 'account':
            accounts = Account.objects.all()
            queryset = queryset.filter(date__gte=date_range[0], date__lte=date_range[1], type__in=transaction_types, account__in=accounts).order_by('-date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()

        if 'account_id' in self.kwargs:
            print("IN")
            context['account_id'] = self.kwargs['account_id']
            print("self.kwargs['account_id']: ", self.kwargs['account_id'])
        else:
            context['account_id'] = None

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

        context['next_url'] = 'transaction_records_list_view'

        context['transactions'] = self.object_list
        # context['transactions'] = [self.format_transaction(transaction) for transaction in transactions_list]
        if self.object_list.count() == 0:
            context['transactions_total'] = 0
        else:
            context['transactions_total'] = round(self.object_list.aggregate(Sum('amount'))['amount__sum'], 2)
        context['base_template'] = 'budgeter/base.html'
        return context

class TransactionRecordDetailView(LoginRequiredMixin, DetailView):
    model = TransactionRecord

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.has_expense_items:
            expense_items = ExpenseItem.objects.filter(transaction_record_id=self.object.id)
            context['expense_items'] = expense_items
        return context

class DeleteTransactionRecordView(LoginRequiredMixin, DeleteView):
    model = TransactionRecord

    def get_success_url(self):
        if self.object.type == 'T':
            try:
                self.transfer_accounts = TransferAccounts.objects.get(user=self.request.user, account_to=self.object)
            except:
                self.transfer_accounts = TransferAccounts.objects.get(user=self.request.user, account_from=self.object)

            if self.transfer_accounts.account_to == self.object:
                self.delete_record = TransactionRecord.objects.get(user=self.request.user, id=self.transfer_accounts.account_from.id)
            else:
                self.delete_record = TransactionRecord.objects.get(user=self.request.user, id=self.transfer_accounts.account_to.id)
            self.update_balances()
            self.delete_record.delete()
            self.transfer_accounts.delete()
        if self.object.type == 'C':
            try:
                self.credit_card_payment = CreditCardPayment.objects.get(user=self.request.user, account=self.object)
            except:
                self.credit_card_payment = CreditCardPayment.objects.get(user=self.request.user, credit_card=self.object)

            print("self.credit_card_payment: ", self.credit_card_payment)
            print("self.credit_card_payment.account: ", self.credit_card_payment.account)
            print("self.credit_card_payment.credit_card: ", self.credit_card_payment.credit_card)
            if self.credit_card_payment.account == self.object:
                self.delete_record = TransactionRecord.objects.get(user=self.request.user, id=self.credit_card_payment.credit_card.id)
            else:
                self.delete_record = TransactionRecord.objects.get(user=self.request.user, id=self.credit_card_payment.account.id)
            self.update_balances()
            self.delete_record.delete()
            self.credit_card_payment.delete()
        return reverse('dashboard', kwargs = { 'pk': self.object.id })

    def update_balances(self):
        print("self.object.type: ", self.object.type)
        if self.object.type == 'X' or self.object.type == 'W':
            if self.object.account:
                print("ACCOUNT")
                account = Account.objects.get(user=self.request.user, id=self.object.account.id)
                account.balance += self.object.amount
                account.save()
            if self.object.credit_card:
                print("CREDIT_CARD")
                if self.object.type == 'C':
                    print("PAYMENT")
                    credit_card = CreditCard.objects.get(user=self.request.user, id=self.object.credit_card.id)
                    credit_card.balance += self.object.amount
                    credit_card.save()
                else:
                    print("ELSE")
                    credit_card = CreditCard.objects.get(user=self.request.user, id=self.object.credit_card.id)
                    credit_card.balance -= self.object.amount
                    credit_card.save()
        elif self.object.type == 'C':
            print("self.credit_card_payment.account: ", self.credit_card_payment.account.account)
            print("self.credit_card_payment.credit_card: ", self.credit_card_payment.credit_card.credit_card)
            account = Account.objects.get(user=self.request.user, id=self.credit_card_payment.account.account.id)
            account.balance += self.object.amount
            account.save()
            credit_card = CreditCard.objects.get(user=self.request.user, id=self.credit_card_payment.credit_card.credit_card.id)
            credit_card.balance += self.object.amount
            credit_card.save()
        elif self.object.type == 'D':
            account = Account.objects.get(user=self.request.user, id=self.object.account.id)
            account.balance -= self.object.amount
            account.save()
        elif self.object.type == 'T':
            print("self.transfer_accounts.account_to.id: ", self.transfer_accounts.account_to.id)
            print("self.transfer_accounts.account_from.id: ", self.transfer_accounts.account_from.id)
            account_to = Account.objects.get(user=self.request.user, id=self.transfer_accounts.account_to.account.id)
            account_from = Account.objects.get(user=self.request.user, id=self.transfer_accounts.account_from.account.id)
            amount = self.object.amount
            account_to.balance += amount
            account_to.save()
            account_from.balance -= amount
            account_from.save()

        return

class UpdateTransactionRecordView(LoginRequiredMixin, FormView):
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
        if transaction_record.type == 'C':
            print("self.request.POST.get('credit_card'): ", self.request.POST.get('credit_card'))
            credit_card_ids = [(transaction_record.credit_card.id, transaction_record.credit_card.name)]
        else:
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
            if self.request.POST.get('credit_card') is not '':
                if transaction_record.amount != self.request.POST.get('amount'):
                    self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount) * -1)
                    self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')))
                    print("FUCK")
                    # self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount) - Decimal(self.request.POST.get('amount')))

        elif transaction_record.ledger_type == 'D':
            print("DEBIT")
            print("transaction_record.amount: ", transaction_record.amount)
            print("self.request.POST.get('amount'): ", self.request.POST.get('amount'))
            if transaction_record.type is 'C':
                if transaction_record.amount != self.request.POST.get('amount'):
                    self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
                    self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
                    # self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
                    self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) - Decimal(transaction_record.amount))
                    # self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')))
            elif transaction_record.type is 'X' or transaction_record.type is 'W':
                if self.request.POST.get('account') is not '':
                    if transaction_record.amount != self.request.POST.get('amount'):
                        if transaction_record.credit_card is None:
                            self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
                        else:
                            self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
                        self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
                if self.request.POST.get('credit_card') is not '':
                    if transaction_record.amount != self.request.POST.get('amount'):
                        if transaction_record.account is None:
                            self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
                            self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
                        else:
                            print("self.request.POST.get('account'): ", self.request.POST.get('account'), ": ", type(self.request.POST.get('account')))
                            self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
                            self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
                            # self.update_account_balance(int(self.request.POST.get('account')), Decimal(self.request.POST.get('amount')))

                ######################
            # if self.request.POST.get('account') is not '':
            #     if transaction_record.amount != self.request.POST.get('amount'):
            #         if transaction_record.credit_card is None:
            #             print("ACCOUNT --->>>>")
            #             self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
            #         else:
            #             print("CREDIT CARD--->>>>")
            #             self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
            #         self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
            # if self.request.POST.get('credit_card') is not '':
            #     if transaction_record.amount != self.request.POST.get('amount'):
            #         if transaction_record.type == 'C':
            #             print("FUCK MY LIFE")
            #             self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) - Decimal(transaction_record.amount))
                        # self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')))
                    # elif transaction_record.type == 'X':
                    #     if transaction_record.account is None:
                    #         self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
                    #         self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
                    #     else:
                    #         print("self.request.POST.get('account'): ", self.request.POST.get('account'), ": ", type(self.request.POST.get('account')))
                    #         self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
                    #         self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
                            # self.update_account_balance(int(self.request.POST.get('account')), Decimal(self.request.POST.get('amount')))

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
        print("account_id: ", account_id)
        account = Account.objects.get(id=account_id)
        account.balance += difference
        account.save()
        print("account balance: ", account.balance)
        return

    def update_credit_card_balance(self, credit_card_id, difference):
        print("update_credit_card_balance")
        print("difference: ", difference)
        credit_card = CreditCard.objects.get(id=credit_card_id)
        print("CREDIT CARD BALANCE BEFORE: ", credit_card.balance)
        credit_card.balance -= difference
        credit_card.save()
        print("CREDIT CARD BALANCE AFTER: ", credit_card.balance)
        return

    # def get_success_url(self):
    #     return reverse('index')


class ExpenseItemCreateView(LoginRequiredMixin, CreateView):
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

class ExpenseItemUpdateView(LoginRequiredMixin, UpdateView):
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

class ExpenseItemDeleteView(LoginRequiredMixin, DeleteView):
    model = ExpenseItem

    def get_success_url(self):
        return reverse('transaction_record_detail_view', kwargs={ 'pk': self.object.transaction_record.id })


class ExpenseItemListView(LoginRequiredMixin, ListView):
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
