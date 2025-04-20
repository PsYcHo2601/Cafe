from rest_framework import serializers
from .models import Dish, Services


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = '__all__'
        read_only_fields = ('id', 'date')


class DishSerializer(serializers.ModelSerializer):
    # Для отображения дополнительной информации о связанных объектах
    creator = serializers.StringRelatedField()
    moderator = serializers.StringRelatedField()

    # Если нужно отображать полную информацию о связанных услугах
    # services = ServicesSerializer(many=True, read_only=True)

    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id',
            'status',
            'status_display',
            'created_at',
            'creator',
            'formed_at',
            'completed_at',
            'moderator',
            'table_number',
            'total_sum',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'formed_at',
            'completed_at',
            'status_display',
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()


class DishCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = [
            'status',
            'table_number',
            'total_sum',
        ]
        # Дополнительные настройки валидации при необходимости
