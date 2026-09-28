from datetime import date
import re

from django.test import Client, TestCase
from django.urls import reverse

from .models import Account, Card, Transaction, User


class BankingViewsTests(TestCase):
	def setUp(self):
		self.sender = self.create_user('1111111111')
		self.recipient = self.create_user('2222222222')
		self.sender_account = self.create_account(self.sender, 'Alex', 'Sender', 'PASS-1')
		self.recipient_account = self.create_account(self.recipient, 'Riley', 'Receiver', 'PASS-2')
		self.sender_card = self.create_card(self.sender_account, '1111222233334444', '1234', '111')
		self.recipient_card = self.create_card(self.recipient_account, '5555666677778888', '5678', '222')
		self.client.force_login(self.sender)

	def create_user(self, phone_number):
		user = User(phone_number=phone_number)
		user.set_password('BankPass123!')
		user.save()
		return user

	def create_account(self, user, first_name, last_name, passport_id):
		return Account.objects.create(
			user=user,
			first_name=first_name,
			last_name=last_name,
			address='1 Main Street',
			passport_id=passport_id,
		)

	def create_card(self, account, card_number, cvv, pin):
		return Card.objects.create(
			account=account,
			card_number=card_number,
			cvv=cvv,
			date=date(2030, 12, 31),
			type='korti_milli',
			PIN=pin,
		)

	def test_account_and_card_defaults(self):
		self.assertEqual(self.sender_account.balance, 1000)
		self.assertEqual(self.sender_card.balance, 500)
		self.assertEqual(self.sender_card.type, 'korti_milli')

	def test_card_credentials_are_generated(self):
		card = Card.objects.create(account=self.sender_account, date=date(2030, 12, 31))
		self.assertRegex(card.card_number, r'^\d{16}$')
		self.assertRegex(card.cvv, r'^\d{3}$')
		self.assertRegex(card.PIN, r'^\d{4}$')

	def test_registration_and_phone_number_login(self):
		self.client.logout()
		response = self.client.post(reverse('register'), {
			'phone_number': '3333333333',
			'password1': 'BankPass123!Secure',
			'password2': 'BankPass123!Secure',
		})
		self.assertEqual(response.status_code, 302)

		response = self.client.post(reverse('login'), {
			'username': '3333333333',
			'password': 'BankPass123!Secure',
		})
		self.assertEqual(response.status_code, 302)
		self.assertTrue(User.objects.filter(phone_number='3333333333').exists())

	def test_user_can_only_access_their_own_cards(self):
		response = self.client.get(reverse('card-detail', args=[self.recipient_card.pk]))
		self.assertEqual(response.status_code, 404)

		response = self.client.post(reverse('card-delete', args=[self.recipient_card.pk]))
		self.assertEqual(response.status_code, 404)
		self.assertTrue(Card.objects.filter(pk=self.recipient_card.pk).exists())

	def test_authenticated_pages_render(self):
		urls = [
			reverse('home'),
			reverse('account-detail'),
			reverse('account-update'),
			reverse('card-list'),
			reverse('card-detail', args=[self.sender_card.pk]),
			reverse('card-update', args=[self.sender_card.pk]),
			reverse('card-delete', args=[self.sender_card.pk]),
			reverse('card-history', args=[self.sender_card.pk]),
			reverse('transfer'),
			reverse('transaction-history'),
			reverse('check-phone'),
			reverse('check-card'),
		]
		for url in urls:
			with self.subTest(url=url):
				self.assertEqual(self.client.get(url).status_code, 200)

	def test_all_four_transfer_combinations_update_balances(self):
		transfers = [
			('account', '', self.recipient.phone_number, '10.00'),
			('account', '', self.recipient_card.card_number, '20.00'),
			('card', self.sender_card.pk, self.recipient.phone_number, '30.00'),
			('card', self.sender_card.pk, self.recipient_card.card_number, '40.00'),
		]
		for source_type, card_id, recipient_id, amount in transfers:
			response = self.client.post(reverse('transfer'), {
				'source_type': source_type,
				'source_card': card_id,
				'recipient_identifier': recipient_id,
				'amount': amount,
			})
			self.assertEqual(response.status_code, 302)

		self.sender_account.refresh_from_db()
		self.sender_card.refresh_from_db()
		self.recipient_account.refresh_from_db()
		self.recipient_card.refresh_from_db()
		self.assertEqual(self.sender_account.balance, 970)
		self.assertEqual(self.sender_card.balance, 430)
		self.assertEqual(self.recipient_account.balance, 1040)
		self.assertEqual(self.recipient_card.balance, 560)
		self.assertEqual(Transaction.objects.count(), 4)

	def test_transfer_form_works_with_csrf_checks_enabled(self):
		csrf_client = Client(enforce_csrf_checks=True)
		csrf_client.force_login(self.sender)
		response = csrf_client.get(reverse('transfer'))
		self.assertEqual(response.status_code, 200)
		token = response.cookies['csrftoken'].value
		self.assertNotRegex(response.content.decode(), r'name="source_account"')
		response = csrf_client.post(reverse('transfer'), {
			'csrfmiddlewaretoken': token,
			'source_type': 'account',
			'recipient_identifier': self.recipient.phone_number,
			'amount': '10.00',
		})
		self.assertEqual(response.status_code, 302)

	def test_foreign_source_and_self_transfer_are_rejected(self):
		response = self.client.post(reverse('transfer'), {
			'source_type': 'card',
			'source_card': self.recipient_card.pk,
			'recipient_identifier': self.sender.phone_number,
			'amount': '50.00',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 0)

		response = self.client.post(reverse('transfer'), {
			'source_type': 'account',
			'source_account': self.sender_account.pk,
			'recipient_identifier': self.sender.phone_number,
			'amount': '50.00',
		})
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Transaction.objects.count(), 0)

	def test_card_check_shows_name_without_sensitive_values(self):
		response = self.client.post(reverse('check-card'), {'card_number': self.recipient_card.card_number})
		self.assertContains(response, 'Riley Receiver')
		self.assertNotContains(response, self.recipient_card.cvv)
		self.assertNotContains(response, self.recipient_card.PIN)
		self.assertNotContains(response, str(self.recipient_card.balance))
		self.assertNotContains(response, self.recipient_account.passport_id)

	def test_deleting_card_preserves_transaction_history(self):
		transaction = Transaction.objects.create(
			sender=self.sender,
			receiver=self.recipient,
			source_card=self.sender_card,
			destination_account=self.recipient_account,
			amount=25,
		)
		response = self.client.post(reverse('card-delete', args=[self.sender_card.pk]))
		self.assertEqual(response.status_code, 302)

		transaction.refresh_from_db()
		self.assertIsNone(transaction.source_card)
		self.assertEqual(transaction.amount, 25)
