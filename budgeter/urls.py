from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    # path('add_account', views.CreateAccountView.as_view(), name='add_account'),
    path('add_account/<slug>/', views.CreateAccountView.as_view(), name='add_account'),
    path('view_account', views.AccountListView.as_view(), name='view_account'),
    path('add_transaction_record/<slug>/', views.CreateTransactionRecordView.as_view(), name='add_transaction_record'),
    # path('add_recurring_expense', views.CreateRecurringExpenseView.as_view(), name='add_recurring_expense'),
    path('expense_item_list_view', views.ExpenseItemListView.as_view(), name='expense_item_list_view'),
    path('expense_item_list_view/<pk>/', views.ExpenseItemListView.as_view(), name='expense_item_list_view'),
    path('account_detail/<slug>/<pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    # path('account_detail/<pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('account_detail/<pk>/<transaction_type>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('account_detail/<pk>/<start_date>/<end_date>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('account_detail/<pk>/<start_date>/<end_date>/<transaction_type>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('add_expense_item/<expense_id>/', views.ExpenseItemCreateView.as_view(), name='add_expense_item'),
    # path('add_expense_item/<expense_pk>/', views.ExpenseItemCreateView.as_view(), name='add_expense_item'),
    path('add_transaction', views.AddTransactionView.as_view(), name='add_transaction'),

    path('update_account/<slug>/<pk>/', views.AccountUpdateView.as_view(), name='update_account'),
    path('update_account/<pk>/', views.AccountUpdateView.as_view(), name='update_account'),

    path('transaction_detail_view/<pk>/expense_item_list_view/', views.ExpenseItemListView.as_view(), name='expense_item_list_view'),

    path('create_transaction_record', views.TransactionRecordOptions.as_view(), name='create_transaction_record'),
    # path('create_transaction_record/<slug>/', views.CreateTransactionRecord.as_view(), name='create_transaction_record'),
    path('transaction_records_list_view', views.TransactionRecordsListView.as_view(), name='transaction_records_list_view'),
    path('transaction_records_list_view/<account_id>/', views.TransactionRecordsListView.as_view(), name='transaction_records_list_view'),
    path('transaction_records_list_view/<account_id>/<account_type>/', views.TransactionRecordsListView.as_view(), name='transaction_records_list_view'),
    path('transaction_record_delete_view/<pk>/', views.DeleteTransactionRecordView.as_view(), name='transaction_record_delete_view'),
    path('transaction_record_detail_view/<pk>/', views.TransactionRecordDetailView.as_view(), name='transaction_record_detail_view'),
    path('transaction_record_update_view/<pk>/', views.UpdateTransactionRecordView.as_view(), name='transaction_record_update_view'),
    path('delete_account/<slug>/<pk>/', views.AccountDeleteView.as_view(), name='delete_account'),
    path('delete_account/<pk>/', views.AccountDeleteView.as_view(), name='delete_account'),
    path('create_credit_card/', views.CreateCreditCardView.as_view(), name='create_credit_card'),
    path('update_credit_card/<pk>/', views.UpdateCreditCardView.as_view(), name='update_credit_card'),
    path('credit_card_list_view/', views.CreditCardListView.as_view(), name='credit_card_list_view'),
    path('expense_item_update/<pk>/', views.ExpenseItemUpdateView.as_view(), name='expense_item_update'),
    path('expense_item_delete/<pk>/', views.ExpenseItemDeleteView.as_view(), name='expense_item_delete'),
    path('register', views.UserCreationView.as_view(), name='register'),
    path('dashboard/<pk>/', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), {'next_page': '/index/'}, name='logout'),
]
