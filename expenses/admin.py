from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "category", "amount", "owner", "created_at")
    list_filter = ("category", "owner")
    search_fields = ("description",)
