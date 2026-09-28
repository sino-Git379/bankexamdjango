from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView
from .forms import AccountForm, CardForm, CheckCardForm, CheckPhoneForm, PhoneAuthenticationForm, RegistrationForm, TransferForm
from .models import Account, Card, Transaction, User


class LoginRequiredView:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name = 'bankapp/home.html'


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'bankapp/form.html'
    success_url = reverse_lazy('login')


class BankLoginView(LoginView):
    authentication_form = PhoneAuthenticationForm
    template_name = 'registration/login.html'


class BankLogoutView(LogoutView):
    pass


class AccountCreateView(LoginRequiredView, CreateView):
    form_class = AccountForm
    template_name = 'bankapp/form.html'
    success_url = reverse_lazy('account-detail')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Account.objects.filter(user=request.user).exists():
            return redirect('account-detail')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AccountDetailView(LoginRequiredView, DetailView):
    model = Account
    template_name = 'bankapp/account_detail.html'
    context_object_name = 'account'

    def get_object(self, queryset=None):
        return get_object_or_404(Account, user=self.request.user)


class AccountUpdateView(LoginRequiredView, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'bankapp/form.html'
    success_url = reverse_lazy('account-detail')

    def get_object(self, queryset=None):
        return get_object_or_404(Account, user=self.request.user)


class CardListView(LoginRequiredView, ListView):
    model = Card
    template_name = 'bankapp/card_list.html'
    context_object_name = 'cards'

    def get_queryset(self):
        return Card.objects.filter(account__user=self.request.user)


class CardCreateView(LoginRequiredView, CreateView):
    form_class = CardForm
    template_name = 'bankapp/form.html'
    success_url = reverse_lazy('card-list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not Account.objects.filter(user=request.user).exists():
            return redirect('account-create')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.account = get_object_or_404(Account, user=self.request.user)
        return super().form_valid(form)


class OwnedCardView(LoginRequiredView):
    model = Card

    def get_queryset(self):
        return Card.objects.filter(account__user=self.request.user)


class CardDetailView(OwnedCardView, DetailView):
    template_name = 'bankapp/card_detail.html'
    context_object_name = 'card'


class CardUpdateView(OwnedCardView, UpdateView):
    form_class = CardForm
    template_name = 'bankapp/form.html'
    success_url = reverse_lazy('card-list')


class CardDeleteView(OwnedCardView, DeleteView):
    template_name = 'bankapp/card_confirm_delete.html'
    success_url = reverse_lazy('card-list')


class TransferView(LoginRequiredView, FormView):
    form_class = TransferForm
    template_name = 'bankapp/transfer_form.html'
    success_url = reverse_lazy('transaction-history')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        source = form.cleaned_data['source']
        destination = form.cleaned_data['destination']
        amount = form.cleaned_data['amount']
        source.balance -= amount
        destination.balance += amount
        source.save()
        destination.save()

        source_account = source if isinstance(source, Account) else None
        source_card = source if isinstance(source, Card) else None
        destination_account = destination if isinstance(destination, Account) else None
        destination_card = destination if isinstance(destination, Card) else None
        receiver = destination.user if isinstance(destination, Account) else destination.account.user
        Transaction.objects.create(sender=self.request.user, receiver=receiver, source_account=source_account, source_card=source_card, destination_account=destination_account, destination_card=destination_card, amount=amount)
        return super().form_valid(form)


class TransactionHistoryView(LoginRequiredView, ListView):
    model = Transaction
    template_name = 'bankapp/transaction_history.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        user = self.request.user
        direction = self.request.GET.get('direction', 'all')
        if direction == 'sent':
            return Transaction.objects.filter(sender=user).order_by('-created_at')
        if direction == 'received':
            return Transaction.objects.filter(receiver=user).order_by('-created_at')
        return (Transaction.objects.filter(sender=user) | Transaction.objects.filter(receiver=user)).order_by('-created_at')


class CardTransactionHistoryView(OwnedCardView, ListView):
    template_name = 'bankapp/transaction_history.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        self.card = get_object_or_404(Card.objects.filter(account__user=self.request.user), pk=self.kwargs['pk'])
        direction = self.request.GET.get('direction', 'all')
        if direction == 'sent':
            return Transaction.objects.filter(source_card=self.card).order_by('-created_at')
        if direction == 'received':
            return Transaction.objects.filter(destination_card=self.card).order_by('-created_at')
        return (Transaction.objects.filter(source_card=self.card) | Transaction.objects.filter(destination_card=self.card)).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card'] = self.card
        return context


class CheckPhoneView(LoginRequiredView, FormView):
    form_class = CheckPhoneForm
    template_name = 'bankapp/check_phone.html'

    def form_valid(self, form):
        account = Account.objects.filter(user__phone_number=form.cleaned_data['phone_number']).first()
        return self.render_to_response(self.get_context_data(form=form, checked=True, account=account))


class CheckCardView(LoginRequiredView, FormView):
    form_class = CheckCardForm
    template_name = 'bankapp/check_card.html'

    def form_valid(self, form):
        card = Card.objects.filter(card_number=form.cleaned_data['card_number']).first()
        return self.render_to_response(self.get_context_data(form=form, checked=True, card=card))