from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ExpenseViewSet, LoginView, logout_view

router = DefaultRouter()
router.register(r"expenses", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("login/", LoginView.as_view(), name="api-login"),
    path("logout/", logout_view, name="api-logout"),
    path("", include(router.urls)),
]
