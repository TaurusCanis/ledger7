from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse, resolve
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from budgeter.models import ( AccountBase, BankAccount, Expense,
    ExpenseItem, Deposit, Withdrawal, Adjustment, TransactionRecord, CreditCard,
    TransferAccounts, Category, SubCategory, Description,
    CreditCardPayment )
from decimal import Decimal
from django.db.models import Sum
from datetime import datetime
from django import forms
from budgeter.forms import (TransactionRecordBaseForm,
    TransactionRecordExpenseForm, TransactionRecordTransferForm,
    TransactionRecordCreditCardPaymentForm, TransactionRecordAdjustmentForm,
    AccountSearchForm, CreateBankAccountForm, CreateCreditCardForm, TransactionRecordDepositForm,
    TransactionRecordWithdrawalForm, ExpenseItemForm
)
from django.forms import modelform_factory
from django.forms.models import model_to_dict
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login
from django.db.models import Q
import json


###BUSINESS LOGIC BEGINS#####

class UserData:

    def __init__(self, user):
        self.user = user
        self.account_bases_bank_accounts = AccountBase.objects.filter(user=user, bankaccount__id__isnull=False)
        self.account_bases_credit_cards = AccountBase.objects.filter(user=user, creditcard__id__isnull=False)
        self.bank_accounts = BankAccount.objects.filter(account_base__user=user)
        self.credit_cards = CreditCard.objects.filter(account_base__user=user)
        self.transaction_records = TransactionRecord.objects.filter(user=self.user).order_by('-date')

    def get_available_balance(self):
        self.available_balance = round(self.bank_accounts.filter(exclude_from_available_funds=False).aggregate(Sum('balance'))['balance__sum'], 2) - round(self.credit_cards.aggregate(Sum('balance'))['balance__sum'], 2)
        return self.available_balance

    def get_transaction_records(self, account=None, num_records=None, date_range=None, transaction_types=None):
        qs = self.transaction_records.filter(user=self.user)
        print("QS: ", qs)
        if transaction_types:
            qs = qs.filter(transaction_type__in=transaction_types)
        if account:
            qs = qs.filter(account=account.account_base)
        if date_range:
            qs = qs.filter(date__gte=date_range[0],date__lte=date_range[1])
        if num_records:

            if not qs.exists():
                count = 0
            else:
                count = qs.count()
            if num_records > count:
                qs = qs[:count]
            else:
                qs = qs[count - num_records:count]
        return qs

    def get_transaction_records_total(self, transaction_records):
        if transaction_records:
            if transaction_records.count() == 0:
                return 0
            else:
                return round(transaction_records.aggregate(Sum('amount'))['amount__sum'], 2)
        else:
            return self.get_transaction_records().count()

    def get_credit_card_balances_total(self):
        if self.credit_cards.count() == 0:
            return 0
        else:
            return round(self.credit_cards.aggregate(Sum('account_base__balance'))['account_base__balance__sum'], 2)

    def get_all_accounts(self):
        return [self.bank_accounts, self.credit_cards]

    def get_account_balances_total(self):
        if self.bank_accounts.count() == 0:
            return 0
        else:
            return round(self.bank_accounts.aggregate(Sum('account_base__balance'))['account_base__balance__sum'], 2)

    def get_available_balance(self):
        if self.bank_accounts.count() == 0:
            return 0
        elif self.credit_cards.count() == 0:
            return round(self.bank_accounts.filter(exclude_from_available_funds=False).aggregate(Sum('account_base__balance'))['account_base__balance__sum'], 2)
        else:
            return round(self.bank_accounts.filter(exclude_from_available_funds=False).aggregate(Sum('account_base__balance'))['account_base__balance__sum'], 2) - round(self.credit_cards.aggregate(Sum('account_base__balance'))['account_base__balance__sum'], 2)

    def get_transactions_total_debits(self):
        if self.transaction_records.count() == 0:
            return 0
        else:
            return round(self.transaction_records.aggregate(Sum('amount'))['amount__sum'], 2)

    def get_account_base(self, id):
        return AccountBase.objects.get(id=id)

    def get_all_account_bases(self):
        return AccountBase.objects.filter(user=self.user)

    def set_account_balance(self, id, amount, ledger_type):
        account_base = self.get_account_base(id)

        if hasattr(account_base, 'creditcard'):
            amount *= -1

        if ledger_type == "D":
            account_base.balance -= amount
        else:
            account_base.balance += amount

        account_base.save()
        return

    def get_account(self, id):
        account_base = self.get_account_base(id)
        if hasattr(account_base, "bankaccount"):
            return self.bank_accounts.get(account_base_id=id)
        elif hasattr(account_base, "creditcard"):
            return self.credit_cards.get(account_base_id=id)


####BUSINESS LOGIC ENDS#####

class IndexView(TemplateView):
    template_name = 'budgeter/index.html'

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'budgeter/dashboard.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        transaction_records_list = self.user_data.get_transaction_records(num_records=10)
        context['transaction_records_list'] = transaction_records_list
        credit_cards = self.user_data.credit_cards
        context['credit_cards'] = credit_cards
        accounts = self.user_data.bank_accounts.select_related("account_base")
        context['accounts'] = accounts
        context['credit_cards_total'] = self.user_data.get_credit_card_balances_total()
        context['accounts_total'] = self.user_data.get_account_balances_total()
        context['total_available_funds'] = self.user_data.get_available_balance()
        context['transactions_total_debits'] = self.user_data.get_transactions_total_debits()
        context['base_template'] = 'budgeter/no_base.html'
        return context

def index(request):
    return render(request, "budgeter/index.html")

class UserCreationView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/user_form.html'

    def get_success_url(self):
        user = authenticate(username=self.request.POST.get('username'), password=self.request.POST.get('password1'))
        if user is not None:
            login(self.request, user)
            return reverse('dashboard', kwargs={ 'pk': user.id })

        else:
            return redirect('register')

class LoginView(LoginView):
    def get_success_url(self):
        print("FUCKKKKK YOUOOO")
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class LogoutView(LogoutView):
    next_page = 'index'
    def get_success_url(self):
        return reverse('index')

class CreateAccountView(LoginRequiredMixin, FormView):

    template_name = "budgeter/account_form.html"

    def get_form_class(self):
        if self.kwargs['slug'] == 'bank_account':
            form_class = CreateBankAccountForm
        elif self.kwargs['slug'] == 'credit_card':
            form_class = CreateCreditCardForm
        else:
            return HttpResponse("Form Not Found")
        return form_class

    def form_valid(self, form):
        account_base = AccountBase.objects.create(
            user=self.request.user,
            name=form.cleaned_data['name'],
            balance=form.cleaned_data['balance'],
            account_type=self.kwargs['slug']
        )
        if self.kwargs['slug'] == 'bank_account':
            bank_account = BankAccount.objects.create(
                account_base=account_base,
                type=form.cleaned_data['type'],
                exclude_from_available_funds=form.cleaned_data['exclude_from_available_funds']
            )
        elif self.kwargs['slug'] == 'credit_card':
            credit_card = CreditCard.objects.create(
                account_base=account_base,
                interest_rate=form.cleaned_data['interest_rate'],
            )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class AccountUpdateView(LoginRequiredMixin, FormView):

    template_name = "budgeter/account_update.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)
        self.account_base = self.user_data.get_account_base(self.kwargs['pk'])
        if hasattr(self.account_base, 'bankaccount'):
            self.account_type = 'bank_account'
        elif hasattr(self.account_base, 'creditcard'):
            self.account_type = 'credit_card'

    def get_form_class(self):
        if self.account_type == 'bank_account':
            form_class = CreateBankAccountForm
        elif self.account_type == 'credit_card':
            form_class = CreateCreditCardForm
        else:
            return HttpResponse("Form Not Found")
        return form_class

    def form_valid(self, form):
    ##This probably belongs in the UserData Class
        if self.account_type == 'bank_account':
            bank_account = self.account_base.bankaccount
            bank_account.type=form.cleaned_data['type']
            bank_account.exclude_from_available_funds=form.cleaned_data['exclude_from_available_funds']
            bank_account.save()

        elif self.account_type == 'credit_card':
            credit_card = self.account_base.creditcard
            credit_card.interest_rate=form.cleaned_data['interest_rate']
            credit_card.save()

        self.account_base.name=form.cleaned_data['name']
        self.account_base.balance=form.cleaned_data['balance']
        self.account_base.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['balance'].widget = forms.TextInput(attrs={'class':'form-control'})
        if self.account_type == 'bank_account':
            form.fields['type'].widget = forms.Select(attrs={'class':'form-control'}, choices=[('checking', 'Checking'),('savings', 'Savings'),('cash', 'Cash')])
            form.fields['exclude_from_available_funds'].widget = forms.CheckboxInput(attrs={'class':'form-check-input'})
        return form

    def get_initial(self):
        initial = {}
        initial['name'] = self.account_base.name
        initial['balance'] = self.account_base.balance

        if self.account_type == "credit_card":
            initial['interest_rate'] = self.account_base.creditcard.interest_rate
        return initial

class AccountListView(LoginRequiredMixin, ListView):
    model = BankAccount
    context_object_name = 'accounts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['total_available_funds'] = round(super().get_queryset().aggregate(Sum('balance'))['balance__sum'], 2)
        context['standalone'] = True
        context['base_template'] = 'budgeter/base.html'
        return context

class AccountSearchMixin():

    def get(self, request, *args, **kwargs):
        kwargs={"user_data":self.user_data}
        self.form = AccountSearchForm(**kwargs)
        return self.render_to_response(self.get_context_data(request))

    def post(self, request, *args, **kwargs):
        kwargs={"user_data":self.user_data}
        self.form = AccountSearchForm(self.request.POST, **kwargs)
        self.form.is_valid()
        self.transaction_types = self.form.cleaned_data.get('transaction_type')
        self.date_range = (self.request.POST.get('start_date'), self.request.POST.get('end_date'))
        return self.render_to_response(self.get_context_data(request))

    def get_form_data(self, request, *args, **kwargs):
        context = {}
        if self.request.POST:
            if "account" in self.request.POST != " ":
                self.account = self.user_data.get_account(self.request.POST.get('account'))
                context['account'] = self.account

        context['base_template'] = 'budgeter/base.html'

        # May only be able to view one type of transaction record at a time?
        context['transactions'] = self.user_data.get_transaction_records(self.account, num_records=None, date_range=self.date_range, transaction_types=self.transaction_types)

        context['form'] = self.form
        return context

class AccountDetailView(LoginRequiredMixin, AccountSearchMixin, TemplateView):
    template_name = "budgeter/account_detail.html"
    form_class = AccountSearchForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)
        self.account = self.user_data.get_account(self.kwargs['pk'])
        self.transaction_types = None
        self.date_range = None

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    # def get_initial(self):
    #     print("GET_INITIAL")
    #     initial = super().get_initial()
    #     initial['start_date'], initial['end_date'] = self.get_date_range()
    #     print("INITIAL: ", initial)
    #     return initial

    def get_context_data(self, request, *args, **kwargs):
        context = super().get_context_data()
        context['account'] = self.account
        form_data = super().get_form_data(request, *args, **kwargs)
        for k, v in form_data.items():
            context[k] = v

        return context

class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model = AccountBase
    template_name = "budgeter/account_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        TransactionRecord.objects.filter(account=self.object).delete()
        if hasattr(self.object, "bankaccount"):
            self.object.bankaccount.delete()
        elif hasattr(self.object, "creditcard"):
            self.object.creditcard.delete()
        return super().delete(request, *args, **kwargs)

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

class CreditCardListView(LoginRequiredMixin, ListView):
    model = CreditCard

class TransactionRecordOptions(LoginRequiredMixin, TemplateView):
    template_name = 'budgeter/transaction_record_options.html'

class CreateTransactionRecordView(LoginRequiredMixin, FormView):
    template_name = 'budgeter/transactionrecord_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)

    def get_form_class(self):
        slug = self.kwargs['slug']

        if slug == "expense":
            return TransactionRecordExpenseForm
        elif slug == "creditcardpayment":
            print("SHOULD BE HERE")
            return TransactionRecordCreditCardPaymentForm
        elif slug == "deposit":
            return TransactionRecordDepositForm
        elif slug == "withdrawal":
            return TransactionRecordWithdrawalForm
        elif slug == "transfer":
            return TransactionRecordTransferForm
        else:
            print("BUT ARE WE HERE?")
            return TransactionRecordAdjustmentForm

    def get_initial(self):
        initial = super().get_initial()
        initial['date']= datetime.today()
        return initial

    def get_form_kwargs(self):
        print("******&&&&&&&&%%%%%%get_form_kwargs")
        kwargs = super().get_form_kwargs()
        kwargs.update({
            "user_data": self.user_data,
            "view_type": "create"
        })
        return kwargs

    # def get_form(self):
    #     form = super().get_form()
    #     return form

    # def get_context_data(self, **kwargs):
    #     """Insert the form into the context dict."""
    #     print("HERE_C")
    #     if 'form' not in kwargs:
    #         kwargs['form'] = self.get_form()
    #     return super().get_context_data(**kwargs)

    def get_context_data(self):
        print("HERE_ A")
        context = super().get_context_data()
        print("HERE_B")
        context['bank_accounts'] = self.user_data.bank_accounts

        slug = self.kwargs['slug']
        context['template_extension'] = "budgeter/" + slug + "_form.html"
        context['js_extension'] = 'budgeter/js/' + slug + '_form.js'

        if slug in ['expense', 'credit_card_payment']:
            context['credit_cards'] = self.user_data.credit_cards

        title = " ".join(slug.split("_")).title()
        if slug in ['expense', 'adjustment']:
            context['transaction_record_heading'] = f"Add an %s" % title
        else:
            context['transaction_record_heading'] = f"Add a %s" % title

        print("template_extension: ", context['template_extension'])

        return context

    def form_valid(self, form):
        self.instance = form.create_record(self.user_data)
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.POST.get('has_expense_items'):
            return reverse('add_expense_item', kwargs = { 'expense_id': self.instance.transaction_record.tr_expense.id })
        else:
            return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

class TransactionRecordsListView(LoginRequiredMixin, AccountSearchMixin, TemplateView):
    template_name = "budgeter/transactionrecord_list.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)
        self.account = None
        self.transaction_types = None
        self.date_range = None

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_context_data(self, request, *args, **kwargs):
        context = super().get_context_data()
        form_data = super().get_form_data(request, *args, **kwargs)
        for k, v in form_data.items():
            context[k] = v

        return context

class TransactionRecordDetailView(LoginRequiredMixin, DetailView):
    model = TransactionRecord

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.object, "tr_expense") and self.object.tr_expense.has_expense_items:
            expense_items = ExpenseItem.objects.filter(expense__transaction_record_id=self.object.id)
            context['expense_items'] = expense_items
        return context

class DeleteTransactionRecordView(LoginRequiredMixin, DeleteView):
    model = TransactionRecord

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)
        # self.account = None
        # self.transaction_types = None
        # self.date_range = None

    def get_success_url(self):
        if self.object.ledger_type == "C":
            ledger_type = "D"
        else:
            ledger_type = "C"

        self.object.delete_instance(self.user_data, ledger_type)

        return reverse('dashboard', kwargs = { 'pk': self.object.id })

class UpdateTransactionRecordView(LoginRequiredMixin, FormView):
    model = TransactionRecord
    fields = '__all__'
    template_name = 'budgeter/transactionrecord_form.html'
    success_url = '/budgeter/'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)
        self.transaction_record = TransactionRecord.objects.get(id=self.kwargs['pk'])

    def get_form_class(self):
        if self.transaction_record.transaction_type == "expense":
            return TransactionRecordExpenseForm
        elif self.transaction_record.transaction_type == "creditcardpayment":
            return TransactionRecordCreditCardPaymentForm
        elif self.transaction_record.transaction_type == "deposit":
            return TransactionRecordDepositForm
        elif self.transaction_record.transaction_type == "withdrawal":
            return TransactionRecordWithdrawalForm
        elif self.transaction_record.transaction_type == "transfer":
            return TransactionRecordTransferForm
        else:
            return TransactionRecordAdjustmentForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            "user_data": self.user_data,
            "view_type": "update"
        })
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # transaction_record = self.get_transaction_record()
        for field in TransactionRecord._meta.get_fields():
            print("FIELD: ", field.name, " type: ", type(field))
            if hasattr(self.transaction_record, field.name):
                if field is 'date':
                    initial[field.name] = getattr(self.transaction_record, field.name)
                else:
                    initial[field.name] = getattr(self.transaction_record, field.name)
        print("initial: ", initial)
        return initial

    def get_context_data(self):
        print("FORM CLASS: ", self.get_form_class())
        context = super().get_context_data()
        context['bank_accounts'] = self.user_data.bank_accounts

        # slug = self.kwargs['slug']
        context['template_extension'] = "budgeter/" + self.transaction_record.transaction_type + "_form.html"
        context['js_extension'] = 'budgeter/js/' + self.transaction_record.transaction_type + '_form.js'

        if self.transaction_record.transaction_type in ['expense', 'credit_card_payment']:
            context['credit_cards'] = self.user_data.credit_cards

        title = " ".join(self.transaction_record.transaction_type.split("_")).title()
        if self.transaction_record.transaction_type in ['expense', 'adjustment']:
            context['transaction_record_heading'] = f"Add an %s" % title
        else:
            context['transaction_record_heading'] = f"Add a %s" % title

        print("CONTEXT: ", context['template_extension'])

        return context

    def form_valid(self, form):
        print("FORM VALID")
        print("FORM VALID: ", form.is_valid())
        form.update_instance(self.transaction_record, self.user_data)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("FORM INVALID")
        print("FORM VALID: ", form.is_valid())
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('dashboard', kwargs={ 'pk': self.request.user.id })

    # def change_balance(self):
    #     if self.object.ledger_type == "C":
    #         ledger_type = "D"
    #     else:
    #         ledger_type = "C"
    #
    #     self.object.delete_instance(self.user_data, ledger_type)
    #
    #     #### NOT COMPLETE ####
    #
    #     return reverse('dashboard', kwargs = { 'pk': self.object.id })
    #
    # def form_valid(self, form):
    #     # transaction_record = self.get_transaction_record()
    #     for key, value in model_to_dict(self.transaction_record).items():
    #         print(key, ": ", value)
    #     if self.transaction_record.ledger_type == 'C':
    #         print("CREDIT")
    #         if self.request.POST.get('account') is not '':
    #             print("transaction_record.amount: ", transaction_record.amount, "self.request.POST.get('amount'): ", self.request.POST.get('amount'))
    #             if transaction_record.amount != self.request.POST.get('amount'):
    #                 self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount) * -1)
    #                 self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')))
    #         if self.request.POST.get('credit_card') is not '':
    #             if transaction_record.amount != self.request.POST.get('amount'):
    #                 self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount) * -1)
    #                 self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')))
    #                 print("FUCK")
    #                 # self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount) - Decimal(self.request.POST.get('amount')))
    #
    #     elif transaction_record.ledger_type == 'D':
    #         print("DEBIT")
    #         print("transaction_record.amount: ", transaction_record.amount)
    #         print("self.request.POST.get('amount'): ", self.request.POST.get('amount'))
    #         if transaction_record.type is 'C':
    #             if transaction_record.amount != self.request.POST.get('amount'):
    #                 self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
    #                 self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
    #                 # self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
    #                 self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) - Decimal(transaction_record.amount))
    #                 # self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')))
    #         elif transaction_record.type is 'X' or transaction_record.type is 'W':
    #             if self.request.POST.get('account') is not '':
    #                 if transaction_record.amount != self.request.POST.get('amount'):
    #                     if transaction_record.credit_card is None:
    #                         self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
    #                     else:
    #                         self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
    #                     self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
    #             if self.request.POST.get('credit_card') is not '':
    #                 if transaction_record.amount != self.request.POST.get('amount'):
    #                     if transaction_record.account is None:
    #                         self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
    #                         self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
    #                     else:
    #                         print("self.request.POST.get('account'): ", self.request.POST.get('account'), ": ", type(self.request.POST.get('account')))
    #                         self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
    #                         self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
    #                         # self.update_account_balance(int(self.request.POST.get('account')), Decimal(self.request.POST.get('amount')))
    #
    #             ######################
    #         # if self.request.POST.get('account') is not '':
    #         #     if transaction_record.amount != self.request.POST.get('amount'):
    #         #         if transaction_record.credit_card is None:
    #         #             print("ACCOUNT --->>>>")
    #         #             self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
    #         #         else:
    #         #             print("CREDIT CARD--->>>>")
    #         #             self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
    #         #         self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')) * -1)
    #         # if self.request.POST.get('credit_card') is not '':
    #         #     if transaction_record.amount != self.request.POST.get('amount'):
    #         #         if transaction_record.type == 'C':
    #         #             print("FUCK MY LIFE")
    #         #             self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) - Decimal(transaction_record.amount))
    #                     # self.update_account_balance(self.request.POST.get('account'), Decimal(self.request.POST.get('amount')))
    #                 # elif transaction_record.type == 'X':
    #                 #     if transaction_record.account is None:
    #                 #         self.update_credit_card_balance(transaction_record.credit_card.id, Decimal(transaction_record.amount))
    #                 #         self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
    #                 #     else:
    #                 #         print("self.request.POST.get('account'): ", self.request.POST.get('account'), ": ", type(self.request.POST.get('account')))
    #                 #         self.update_account_balance(transaction_record.account.id, Decimal(transaction_record.amount))
    #                 #         self.update_credit_card_balance(self.request.POST.get('credit_card'), Decimal(self.request.POST.get('amount')) * -1)
    #                         # self.update_account_balance(int(self.request.POST.get('account')), Decimal(self.request.POST.get('amount')))
    #
    #     for key, value in self.request.POST.items():
    #         if key is not 'csrfmiddlewaretoken':
    #             print("key: ", key, " value: ", value, " value type: ", type(value))
    #             if key == 'account':
    #                 print("KEY IS ACCOUNT. VALUE: ", value)
    #                 if value is not '':
    #                     print("ACCOUNT")
    #                     value = Account.objects.get(id=value)
    #                     setattr(transaction_record, key, value)
    #                 else:
    #                     setattr(transaction_record, key, None)
    #             elif key == 'credit_card':
    #                 print("KEY IS CREDIT_CARD. VALUE: ", value)
    #                 if value is not '':
    #                     print("CREDIT_CARD")
    #                     value = CreditCard.objects.get(id=value)
    #                     setattr(transaction_record, key, value)
    #                 else:
    #                     setattr(transaction_record, key, None)
    #             else:
    #                 setattr(transaction_record, key, value)
    #             if value == 'on':
    #                 setattr(transaction_record, key, True)
    #             elif value == 'off':
    #                 setattr(transaction_record, key, False)
    #     transaction_record.save()
    #     for key, value in model_to_dict(transaction_record).items():
    #         print(key, ": ", value)
    #     return super().form_valid(form)
    #
    # def form_invalid(self, form):
    #     print("FORM INVALID")
    #     print(form.errors)
    #     return super().form_invalid(form)
    #
    # def update_account_balance(self, account_id, difference):
    #     print("update_account_balance")
    #     print("account_id: ", account_id)
    #     account = Account.objects.get(id=account_id)
    #     account.balance += difference
    #     account.save()
    #     print("account balance: ", account.balance)
    #     return
    #
    # def update_credit_card_balance(self, credit_card_id, difference):
    #     print("update_credit_card_balance")
    #     print("difference: ", difference)
    #     credit_card = CreditCard.objects.get(id=credit_card_id)
    #     print("CREDIT CARD BALANCE BEFORE: ", credit_card.balance)
    #     credit_card.balance -= difference
    #     credit_card.save()
    #     print("CREDIT CARD BALANCE AFTER: ", credit_card.balance)
    #     return

    # def get_success_url(self):
    #     return reverse('index')


class ExpenseItemCreateView(LoginRequiredMixin, FormView):
    template_name = "budgeter/expenseitem_form.html"
    form_class = ExpenseItemForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.user_data = UserData(self.request.user)

    def get_initial(self):
        initial = super().get_initial()
        initial['expense_id'] = self.kwargs['expense_id']
        return initial

    def form_valid(self, form):
        form.create_expense_item(self.user_data, self.kwargs['expense_id'])
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.request.POST.get('add_new_item') is not None:
            return reverse('add_expense_item', kwargs={'expense_id': self.kwargs['expense_id']})
        else:
            return reverse('transaction_record_detail_view', kwargs={ 'pk': TransactionRecord.objects.get(tr_expense__id=self.kwargs['expense_id']).id })

class ExpenseItemUpdateView(LoginRequiredMixin, UpdateView):
    model = ExpenseItem

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['update_expense_item'] = True
        return context

    def get_form_class(self):
        self.exclude = ['expense']
        return modelform_factory(self.model, exclude=self.exclude)

    def get_form(self, form_class=None):
        print("RIGHT HERE")
        form = super().get_form(form_class)
        form.fields['name'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['amount'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['note'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['category'].widget = forms.TextInput(attrs={'class':'form-control'})
        form.fields['sub_category'].widget = forms.TextInput(attrs={'class':'form-control'})
        return form

    def get_success_url(self):
        return reverse('transaction_record_detail_view', kwargs={ 'pk': self.object.expense.transaction_record.id })

class ExpenseItemDeleteView(LoginRequiredMixin, DeleteView):
    model = ExpenseItem

    def get_success_url(self):
        return reverse(
            'transaction_record_detail_view',
            kwargs={
                'pk': TransactionRecord.objects.get(tr_expense__expenseitem__id=self.kwargs['pk']).id
            }
        )

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
