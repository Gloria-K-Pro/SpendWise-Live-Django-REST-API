# SpendWise Live – Django REST API (instructor reference)

Week 8 reference solution. Django + DRF backend with token auth, per-user scoping, filtering, search, ordering, pagination and CORS.

## Setup
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # users alice / bob, password SpendWise#2026
python manage.py runserver        # http://127.0.0.1:8000
python manage.py test expenses    # 19 tests, all requirement cases
```
Front end: from `spendwise-frontend/` run `python -m http.server 5500`, open http://127.0.0.1:5500.

## Endpoints
| Method | URL | Notes |
|---|---|---|
| POST | `/api/login/` | `{username, password}` → `{token, username}` |
| POST | `/api/logout/` | deletes token |
| GET/POST | `/api/expenses/` | list (paginated, 5/page) / create |
| GET/PUT/PATCH/DELETE | `/api/expenses/<id>/` | own rows only, others → 404 |

Query params: `?category=food`, `?search=coffee`, `?ordering=-amount` (`amount`, `created_at`), `?page=2`, `?page_size=20`.
Header: `Authorization: Token <token>`.

## Env vars (production)
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`.

## Design decisions students usually get wrong
1. **401 vs 403.** Only `TokenAuthentication` is configured. Put `SessionAuthentication` first and anonymous requests return 403, failing the brief.
2. **Scoping lives in `get_queryset`,** not in `list()`. That covers retrieve/update/delete too, so another user's id is a 404.
3. **Owner is set in `perform_create`** and is read-only in the serializer. Sending `"owner": 2` in the body is ignored.
4. **`DecimalField` for money,** with a min of 0.01. Bad input returns 400, never 500.
5. **CORS middleware sits above `CommonMiddleware`,** with explicit origins. Never `CORS_ALLOW_ALL_ORIGINS=True` in production.
