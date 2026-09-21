from rest_framework import serializers

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    # Shown in responses, never accepted from the client.
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = Expense
        fields = ["id", "amount", "description", "category", "created_at", "owner"]
        read_only_fields = ["id", "created_at", "owner"]

    def to_internal_value(self, data):
        # Accept "Food" or " FOOD " from the UI; store "food".
        if hasattr(data, "copy"):
            data = data.copy()
            if isinstance(data.get("category"), str):
                data["category"] = data["category"].strip().lower()
        return super().to_internal_value(data)

    def validate_description(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Description cannot be blank.")
        return value
