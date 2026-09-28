import random

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	username = None
	phone_number = models.CharField(max_length=20, unique=True)

	USERNAME_FIELD = 'phone_number'
	REQUIRED_FIELDS = []


class Account(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	address = models.CharField(max_length=255)
	passport_id = models.CharField(max_length=50, unique=True)
	balance = models.DecimalField(max_digits=12, decimal_places=2, default=1000)

	def __str__(self):
		return f'{self.first_name} {self.last_name}'


class Card(models.Model):
	CARD_TYPES = [
		('korti_milli', 'Korti Milli'),
		('visa', 'Visa'),
		('mastercard', 'Mastercard'),
	]

	account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='cards')
	card_number = models.CharField(max_length=16, unique=True, blank=True, default='')
	cvv = models.CharField(max_length=4, blank=True, default='')
	date = models.DateField()
	type = models.CharField(max_length=11, choices=CARD_TYPES, default='korti_milli')
	PIN = models.CharField(max_length=4, blank=True, default='')
	balance = models.DecimalField(max_digits=12, decimal_places=2, default=500)

	def save(self, *args, **kwargs):
		if not self.card_number:
			self.card_number = str(random.randint(10**15, 10**16 - 1))
		if not self.cvv:
			self.cvv = str(random.randint(100, 999))
		if not self.PIN:
			self.PIN = str(random.randint(1000, 9999))
		super().save(*args, **kwargs)

	def __str__(self):
		return f'Card ending {self.card_number[-4:]}'


class Transaction(models.Model):
	sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
	receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
	source_account = models.ForeignKey(
		Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_transactions'
	)
	source_card = models.ForeignKey(
		Card, on_delete=models.SET_NULL, null=True, blank=True, related_name='outgoing_transactions'
	)
	destination_account = models.ForeignKey(
		Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transactions'
	)
	destination_card = models.ForeignKey(
		Card, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transactions'
	)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.amount} on {self.created_at}'
