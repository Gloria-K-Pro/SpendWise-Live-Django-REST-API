from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    """
    list/create/retrieve/update/destroy for the logged-in user's expenses.

    ?category=food        exact category filter
    ?search=coffee        matches description
    ?ordering=-amount     amount, created_at (prefix - for descending)
    ?page=2&page_size=10  pagination
    """

    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["category"]
    search_fields = ["description"]
    ordering_fields = ["amount", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # The whole security model lives on this line. Every action (list,
        # retrieve, update, delete) goes through it, so another user's
        # expense id returns 404: we don't even confirm it exists.
        return Expense.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # Owner comes from the token, never from the request body.
        serializer.save(owner=self.request.user)


class LoginView(ObtainAuthToken):
    """POST {username, password} -> {token, username}. Open to anonymous users."""

    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)  # bad credentials -> 400, not 500
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": user.username})


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Delete the token so it can't be reused."""
    request.auth.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
