from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Account, Card, User


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone_number',)


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label='Phone number')


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name', 'last_name', 'address', 'passport_id')


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ('date', 'type')
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class TransferForm(forms.Form):
    SOURCE_TYPES = [('account', 'Account'), ('card', 'Card')]

    source_type = forms.ChoiceField(choices=SOURCE_TYPES)
    source_card = forms.ModelChoiceField(queryset=Card.objects.none(), required=False)
    recipient_identifier = forms.CharField(label='Recipient phone or card number', max_length=20)
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['source_card'].queryset = Card.objects.filter(account__user=user)

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type')
        if source_type == 'account':
            source = Account.objects.filter(user=self.user).first()
            if source is None:
                self.add_error('source_type', 'Create an account before transferring money.')
        elif source_type == 'card':
            source = cleaned_data.get('source_card')
        else:
            source = None
        identifier = cleaned_data.get('recipient_identifier')
        amount = cleaned_data.get('amount')

        if source_type == 'card' and source is None:
            self.add_error('source_card', 'Choose a source card.')
        elif source is not None:
            cleaned_data['source'] = source

        if identifier:
            destination_card = Card.objects.filter(card_number=identifier).first()
            if destination_card:
                destination = destination_card
            else:
                recipient = User.objects.filter(phone_number=identifier).first()
                if recipient is None:
                    self.add_error('recipient_identifier', 'Recipient not found.')
                    destination = None
                else:
                    destination = Account.objects.filter(user=recipient).first()
                    if destination is None:
                        self.add_error('recipient_identifier', 'Recipient does not have an account.')
            if destination is not None:
                cleaned_data['destination'] = destination

        if source is not None and amount is not None:
            if amount > source.balance:
                self.add_error('amount', 'Insufficient balance.')
            destination = cleaned_data.get('destination')
            if destination == source:
                self.add_error('recipient_identifier', 'Source and recipient must be different.')

        return cleaned_data


class CheckPhoneForm(forms.Form):
    phone_number = forms.CharField(max_length=20)


class CheckCardForm(forms.Form):
    card_number = forms.CharField(max_length=16)