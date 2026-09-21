"""Every case in the Week 8 'Testing Requirements', plus the ones that bite in real life."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Expense

URL = "/api/expenses/"
User = get_user_model()


class ExpenseAPITests(APITestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pass-alice-123")
        self.bob = User.objects.create_user("bob", password="pass-bob-123")
        self.alice_token = Token.objects.create(user=self.alice)
        self.bob_token = Token.objects.create(user=self.bob)
        rows = [
            ("Morning coffee", "food", "250"),
            ("Coffee beans", "food", "1200"),
            ("Matatu fare", "transport", "100"),
            ("KPLC tokens", "bills", "1500"),
        ]
        for d, c, a in rows:
            Expense.objects.create(owner=self.alice, description=d, category=c, amount=Decimal(a))
        self.bob_expense = Expense.objects.create(
            owner=self.bob, description="Bob's coffee", category="food", amount=Decimal("300")
        )

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    # --- Auth -------------------------------------------------------------
    def test_login_returns_token(self):
        r = self.client.post("/api/login/", {"username": "alice", "password": "pass-alice-123"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["token"], self.alice_token.key)

    def test_login_bad_password_is_400_not_500(self):
        r = self.client.post("/api/login/", {"username": "alice", "password": "wrong"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_no_token_is_401(self):
        r = self.client.get(URL)
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("WWW-Authenticate", r.headers)

    def test_bad_token_is_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
        self.assertEqual(self.client.get(URL).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_kills_token(self):
        self.auth(self.alice_token)
        self.assertEqual(self.client.post("/api/logout/").status_code, 204)
        self.assertEqual(self.client.get(URL).status_code, 401)

    # --- Per-user scoping -------------------------------------------------
    def test_each_user_sees_only_their_own(self):
        self.auth(self.alice_token)
        alice = self.client.get(URL, {"page_size": 100}).data
        self.assertEqual(alice["count"], 4)
        self.assertTrue(all(row["owner"] == "alice" for row in alice["results"]))

        self.auth(self.bob_token)
        bob = self.client.get(URL).data
        self.assertEqual(bob["count"], 1)
        self.assertEqual(bob["results"][0]["description"], "Bob's coffee")

    def test_cannot_read_update_or_delete_someone_elses_row(self):
        self.auth(self.alice_token)
        detail = f"{URL}{self.bob_expense.id}/"
        self.assertEqual(self.client.get(detail).status_code, 404)
        self.assertEqual(self.client.patch(detail, {"amount": "1"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(detail).status_code, 404)
        self.assertTrue(Expense.objects.filter(id=self.bob_expense.id).exists())

    def test_owner_comes_from_token_not_body(self):
        self.auth(self.alice_token)
        payload = {"amount": "99.50", "description": "Chai", "category": "Food", "owner": self.bob.id}
        r = self.client.post(URL, payload, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["owner"], "alice")
        self.assertEqual(r.data["category"], "food")  # normalised
        self.assertEqual(Expense.objects.get(id=r.data["id"]).owner, self.alice)

    # --- Filtering, search, ordering, pagination --------------------------
    def test_filter_by_category(self):
        self.auth(self.alice_token)
        rows = self.client.get(URL, {"category": "food"}).data["results"]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r["category"] == "food" for r in rows))

    def test_search_description(self):
        self.auth(self.alice_token)
        rows = self.client.get(URL, {"search": "coffee"}).data["results"]
        self.assertEqual({r["description"] for r in rows}, {"Morning coffee", "Coffee beans"})

    def test_ordering_by_amount_desc_and_asc(self):
        self.auth(self.alice_token)
        desc = [Decimal(r["amount"]) for r in self.client.get(URL, {"ordering": "-amount"}).data["results"]]
        asc = [Decimal(r["amount"]) for r in self.client.get(URL, {"ordering": "amount"}).data["results"]]
        self.assertEqual(desc, sorted(desc, reverse=True))
        self.assertEqual(asc, sorted(asc))

    def test_ordering_by_created_at(self):
        self.auth(self.alice_token)
        stamps = [r["created_at"] for r in self.client.get(URL, {"ordering": "created_at"}).data["results"]]
        self.assertEqual(stamps, sorted(stamps))

    def test_pagination_envelope(self):
        for i in range(6):  # alice now has 10 rows, page size is 5
            Expense.objects.create(owner=self.alice, description=f"Extra {i}", category="other", amount=1)
        self.auth(self.alice_token)
        page1 = self.client.get(URL).data
        self.assertEqual(set(page1), {"count", "next", "previous", "results"})
        self.assertEqual(page1["count"], 10)
        self.assertEqual(len(page1["results"]), 5)
        self.assertIsNone(page1["previous"])
        self.assertIsNotNone(page1["next"])
        page2 = self.client.get(URL, {"page": 2}).data
        self.assertIsNone(page2["next"])
        self.assertIsNotNone(page2["previous"])

    def test_filters_combine(self):
        self.auth(self.alice_token)
        rows = self.client.get(URL, {"category": "food", "search": "coffee", "ordering": "-amount"}).data["results"]
        self.assertEqual([r["description"] for r in rows], ["Coffee beans", "Morning coffee"])

    # --- Week 6 discipline: bad input is a clean 400, never a 500 ---------
    def test_bad_input_is_400(self):
        self.auth(self.alice_token)
        cases = [
            {"amount": "abc", "description": "x", "category": "food"},
            {"amount": "-5", "description": "x", "category": "food"},
            {"amount": "0", "description": "x", "category": "food"},
            {"amount": "10", "description": "   ", "category": "food"},
            {"amount": "10", "description": "x", "category": "not-a-category"},
            {},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(URL, payload, format="json").status_code, 400)

    def test_malformed_json_is_400(self):
        self.auth(self.alice_token)
        r = self.client.post(URL, data="{not json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_unknown_category_filter_is_400(self):
        self.auth(self.alice_token)
        self.assertEqual(self.client.get(URL, {"category": "nonsense"}).status_code, 400)

    # --- CORS -------------------------------------------------------------
    def test_cors_allows_dashboard_origin(self):
        r = self.client.options(
            URL,
            HTTP_ORIGIN="http://127.0.0.1:5500",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )
        self.assertEqual(r.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:5500")

    def test_cors_blocks_unknown_origin(self):
        r = self.client.get(URL, HTTP_ORIGIN="https://evil.example")
        self.assertNotIn("Access-Control-Allow-Origin", r.headers)
