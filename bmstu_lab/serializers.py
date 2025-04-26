from collections import OrderedDict

from rest_framework import serializers
from .models import Dish, Services, OrderServices, CustomUser
from django.urls import reverse


class ServicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Services
        fields = ['id', 'name', 'description', 'price', 'date', 'is_active']
        read_only_fields = ['is_active']

    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']


class ServicesListSerializer(ServicesSerializer):
    draft_id = serializers.SerializerMethodField()
    in_draft_count = serializers.IntegerField()
    image_url = serializers.SerializerMethodField()

    class Meta(ServicesSerializer.Meta):
        fields = ServicesSerializer.Meta.fields + ['draft_id', 'in_draft_count', 'image_url']

    def get_draft_id(self, obj):
        return self.context.get('draft_id')

    def get_image_url(self, obj):
        if obj.image_url:
            return obj.image_url
        return None


class ServicesImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

    def validate_image(self, value):
        if value.size > 2 * 1024 * 1024:  # 2MB
            raise serializers.ValidationError("Image size should not exceed 2MB")
        return value


class AddToDraftSerializer(serializers.Serializer):
    guest_name = serializers.CharField(max_length=255, required=False, default="")


class DishSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField()
    moderator = serializers.StringRelatedField()
    services = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Dish
        fields = [
            'id', 'status', 'status_display', 'created_at', 'creator',
            'formed_at', 'completed_at', 'moderator', 'table_number',
            'total_sum', 'services'
        ]

    def get_services(self, obj):
        services = OrderServices.objects.filter(order=obj).select_related('service')
        return OrderServiceSerializer(services, many=True).data


class DishListSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField()
    moderator = serializers.StringRelatedField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    services_count = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id', 'status', 'status_display', 'created_at', 'creator',
            'formed_at', 'moderator', 'table_number', 'services_count'
        ]

    def get_services_count(self, obj):
        return OrderServices.objects.filter(order_id=obj.id).count()


class CreateDishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['table_number']

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class UpdateDishStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['status']

    def validate_status(self, value):
        if value not in [Dish.COMPLETED, Dish.REJECTED]:
            raise serializers.ValidationError("Invalid status for this action")
        return value


class OrderServiceSerializer(serializers.ModelSerializer):
    service = ServicesSerializer()
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Services.objects.filter(is_active=True),
        write_only=True,
        source='service'
    )

    class Meta:
        model = OrderServices
        fields = ['id', 'service', 'service_id', 'is_main', 'order_number', 'guest_name']
        read_only_fields = ['id', 'order_number']


class FormDishSerializer(serializers.Serializer):
    def validate(self, data):
        instance = self.instance
        if not instance.orderservices.exists():
            raise serializers.ValidationError("Cannot form an empty dish")
        if not instance.table_number:
            raise serializers.ValidationError("Table number is required")
        return data


class CompleteDishSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=[Dish.COMPLETED, Dish.REJECTED])

    class Meta:
        model = Dish
        fields = ['status']

    def validate(self, data):
        if self.instance.status != Dish.FORMED:
            raise serializers.ValidationError("Only formed dishes can be completed")
        return data