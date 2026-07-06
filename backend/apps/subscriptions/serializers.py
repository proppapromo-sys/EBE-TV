from rest_framework import serializers

from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ("id", "code", "interval", "price_cents", "price", "currency")

    def get_price(self, obj):
        return round(obj.price_cents / 100, 2)
