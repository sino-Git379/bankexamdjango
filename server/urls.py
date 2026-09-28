"""
URL configuration for server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bankapp.views import (
    AccountCreateView,
    AccountDetailView,
    AccountUpdateView,
    BankLoginView,
    BankLogoutView,
    CardCreateView,
    CardDeleteView,
    CardDetailView,
    CardListView,
    CardTransactionHistoryView,
    CardUpdateView,
    CheckCardView,
    CheckPhoneView,
    HomeView,
    RegisterView,
    TransactionHistoryView,
    TransferView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', BankLoginView.as_view(), name='login'),
    path('logout/', BankLogoutView.as_view(), name='logout'),
    path('account/create/', AccountCreateView.as_view(), name='account-create'),
    path('account/', AccountDetailView.as_view(), name='account-detail'),
    path('account/edit/', AccountUpdateView.as_view(), name='account-update'),
    path('cards/', CardListView.as_view(), name='card-list'),
    path('cards/create/', CardCreateView.as_view(), name='card-create'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card-detail'),
    path('cards/<int:pk>/edit/', CardUpdateView.as_view(), name='card-update'),
    path('cards/<int:pk>/delete/', CardDeleteView.as_view(), name='card-delete'),
    path('cards/<int:pk>/transactions/', CardTransactionHistoryView.as_view(), name='card-history'),
    path('transfer/', TransferView.as_view(), name='transfer'),
    path('transactions/', TransactionHistoryView.as_view(), name='transaction-history'),
    path('check/phone/', CheckPhoneView.as_view(), name='check-phone'),
    path('check/card/', CheckCardView.as_view(), name='check-card'),
]
