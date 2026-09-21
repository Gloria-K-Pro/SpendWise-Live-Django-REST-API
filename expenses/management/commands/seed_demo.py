"""python manage.py seed_demo  -> two users with separate data for the demo."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

from expenses.models import Expense

DEMO_PASSWORD = "SpendWise#2026"

ALICE_ROWS = [
    ("Morning coffee", "food", "250"),
    ("Coffee beans 500g", "food", "1200"),
    ("Lunch at canteen", "food", "400"),
    ("Matatu to town", "transport", "100"),
    ("Boda boda home", "transport", "150"),
    ("KPLC tokens", "bills", "1500"),
    ("Safaricom bundles", "bills", "1000"),
    ("Movie night", "entertainment", "800"),
]
BOB_ROWS = [
    ("Groceries", "food", "3200"),
    ("Pharmacy", "health", "650"),
]


class Command(BaseCommand):
    help = "Create two demo users (alice, bob) with separate expenses."

    def handle(self, *args, **options):
        User = get_user_model()
        for username, rows in (("alice", ALICE_ROWS), ("bob", BOB_ROWS)):
            user, created = User.objects.get_or_create(username=username)
            user.set_password(DEMO_PASSWORD)
            user.save()
            Expense.objects.filter(owner=user).delete()
            Expense.objects.bulk_create(
                Expense(owner=user, description=d, category=c, amount=Decimal(a)) for d, c, a in rows
            )
            token, _ = Token.objects.get_or_create(user=user)
            self.stdout.write(f"{username}: {len(rows)} expenses, token {token.key}")
        self.stdout.write(self.style.SUCCESS(f"Password for both users: {DEMO_PASSWORD}"))
