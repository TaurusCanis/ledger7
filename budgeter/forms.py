from django.forms import ModelForm, DateInput
from budgeter.models import Expense, Account, TransactionRecord
from django import forms
from datetime import datetime

class TransactionRecordBaseForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'class' : 'form-control'}))
    amount = forms.DecimalField(decimal_places=2, max_digits=7, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    account = forms.CharField(required=False, widget=forms.HiddenInput())
    #add timestamp?
    exclude_from_accounting = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class":"form-check-input", "type":"checkbox"}))
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={'class' : 'form-control'}))

class TransactionRecordExpenseForm(TransactionRecordBaseForm):
    credit_card = forms.CharField(required=False, widget=forms.HiddenInput())
    category = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    sub_category = forms.CharField(required=False, max_length=200, widget=forms.TextInput(attrs={'class' : 'form-control'}))
    has_expense_items = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class":"form-check-input", "type":"checkbox"}))

class TransactionRecordCreditCardPaymentForm(TransactionRecordBaseForm):
    credit_card = forms.CharField(required=False, widget=forms.HiddenInput())

class TransactionRecordTransferForm(TransactionRecordBaseForm):
    transfer_to_account = forms.CharField(required=False, widget=forms.HiddenInput())
