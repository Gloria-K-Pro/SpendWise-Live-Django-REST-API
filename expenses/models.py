from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import models


class Expense(models.Model):
    """One spending record. Week 7's dict {category, amount} made persistent."""

    class Category(models.TextChoices):
        FOOD = "food", "Food"
        TRANSPORT = "transport", "Transport"
        BILLS = "bills", "Bills"
        SHOPPING = "shopping", "Shopping"
        ENTERTAINMENT = "entertainment", "Entertainment"
        HEALTH = "health", "Health"
        OTHER = "other", "Other"

    # DecimalField, never FloatField, for money: 0.1 + 0.2 must equal 0.3.
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
    )

    class Meta:
        ordering = ["-created_at", "-id"]  # newest first; stable order for pagination

    def __str__(self):
        return f"{self.owner} | {self.category} | {self.amount} | {self.description}"
