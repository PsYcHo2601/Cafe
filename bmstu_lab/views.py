from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from .models import Dish, Services, OrderServices
from .serializers import (
    ServicesSerializer,
    DishSerializer,
    CreateDishSerializer,
    UpdateDishStatusSerializer,
    ServicesListSerializer,
    DishListSerializer
)
from django.conf import settings
import uuid
import io

MINIO_URL = "http://localhost:9000/cafe"


class ServicesListView(APIView):
    def get(self, request):
        # Фильтрация услуг
        services = Services.objects.filter(is_active=True)

        # Получаем черновик заявки пользователя
        user_draft = Dish.objects.filter(
            creator=request.user,
            status=Dish.DRAFT
        ).first()

        # Аннотируем количество услуг в заявке
        if user_draft:
            services = services.annotate(
                in_draft_count=Count(
                    'orderservices',
                    filter=models.Q(orderservices__order=user_draft)
                )
            else:
            services = services.annotate(in_draft_count=models.Value(0, output_field=models.IntegerField()))

            serializer = ServicesListSerializer(services, many=True, context={
                'draft_id': user_draft.id if user_draft else None
            })
        return Response(serializer.data)

    def post(self, request):
        serializer = ServicesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServicesDetailView(APIView):
    def get(self, request, pk):
        service = get_object_or_404(Services, pk=pk, is_active=True)
        serializer = ServicesSerializer(service)
        return Response(serializer.data)

    def put(self, request, pk):
        service = get_object_or_404(Services, pk=pk)
        serializer = ServicesSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        service = get_object_or_404(Services, pk=pk)

        # Удаление изображения из Minio
        if service.image_url:
            try:
                bucket_name, object_name = parse_minio_url(service.image_url)
                minio_client.remove_object(bucket_name, object_name)
            except Exception as e:
                pass  # Логируем ошибку, но продолжаем удаление

        service.is_active = False
        service.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServicesImageUploadView(APIView):
    def post(self, request, pk):
        service = get_object_or_404(Services, pk=pk)

        if 'image' not in request.FILES:
            return Response(
                {"error": "No image provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = request.FILES['image']
        file_extension = image_file.name.split('.')[-1]
        object_name = f"services/{pk}/{uuid.uuid4()}.{file_extension}"

        try:
            # Удаляем старое изображение если есть
            if service.image_url:
                bucket_name, old_object_name = parse_minio_url(service.image_url)
                minio_client.remove_object(bucket_name, old_object_name)

            # Загружаем новое изображение
            minio_client.put_object(
                settings.MINIO_BUCKET,
                object_name,
                io.BytesIO(image_file.read()),
                length=image_file.size,
                content_type=image_file.content_type
            )

            # Обновляем URL изображения в сервисе
            service.image_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{object_name}"
            service.save()

            return Response({"image_url": service.image_url}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddToDraftView(APIView):
    def post(self, request, service_id):
        # Находим или создаем черновик
        draft, created = Dish.objects.get_or_create(
            creator=request.user,
            status=Dish.DRAFT,
            defaults={
                'table_number': 0,
                'total_sum': 0
            }
        )

        service = get_object_or_404(Services, pk=service_id, is_active=True)

        # Добавляем услугу в заявку
        order_service, created = OrderServices.objects.get_or_create(
            order=draft,
            service=service,
            defaults={
                'guest_name': request.data.get('guest_name', ''),
                'order_number': OrderServices.objects.filter(order=draft).count() + 1
            }
        )

        if not created:
            return Response(
                {"detail": "Услуга уже в заявке"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем сумму заявки
        draft.total_sum += service.price
        draft.save()

        return Response(
            {"draft_id": draft.id, "service_added": service_id},
            status=status.HTTP_201_CREATED
        )


class DishListView(APIView):
    def get(self, request):
        # Фильтрация - исключаем удаленные и черновики
        dishes = Dish.objects.exclude(
            status__in=[Dish.DELETED, Dish.DRAFT]
        )

        # Фильтрация по дате формирования
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from and date_to:
            dishes = dishes.filter(
                formed_at__date__range=[date_from, date_to]
            )

        # Фильтрация по статусу
        status_filter = request.query_params.get('status')
        if status_filter:
            dishes = dishes.filter(status=status_filter)

        serializer = DishListSerializer(dishes, many=True)
        return Response(serializer.data)


class DishDetailView(APIView):
    def get(self, request, pk):
        dish = get_object_or_404(Dish, pk=pk)
        serializer = DishSerializer(dish)
        return Response(serializer.data)

    def put(self, request, pk):
        dish = get_object_or_404(Dish, pk=pk)

        if dish.status != Dish.DRAFT:
            return Response(
                {"detail": "Можно изменять только черновики"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CreateDishSerializer(dish, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        dish = get_object_or_404(Dish, pk=pk)

        if dish.status != Dish.DRAFT:
            return Response(
                {"detail": "Можно удалять только черновики"},
                status=status.HTTP_400_BAD_REQUEST
            )

        dish.status = Dish.DELETED
        dish.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FormDishView(APIView):
    def put(self, request, pk):
        dish = get_object_or_404(Dish, pk=pk, creator=request.user)

        if dish.status != Dish.DRAFT:
            return Response(
                {"detail": "Можно формировать только черновики"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка обязательных полей
        required_fields = ['table_number']
        for field in required_fields:
            if not getattr(dish, field):
                return Response(
                    {"detail": f"Не заполнено обязательное поле: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Проверка что есть хотя бы одна услуга
        if not dish.orderservices.exists():
            return Response(
                {"detail": "Нельзя сформировать пустую заявку"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем статус и дату формирования
        dish.status = Dish.FORMED
        dish.formed_at = timezone.now()
        dish.save()

        return Response(DishSerializer(dish).data)


class CompleteDishView(APIView):
    def put(self, request, pk):
        dish = get_object_or_404(Dish, pk=pk)

        if not request.user.is_staff:
            return Response(
                {"detail": "Только для модераторов"},
                status=status.HTTP_403_FORBIDDEN
            )

        if dish.status != Dish.FORMED:
            return Response(
                {"detail": "Можно завершать только сформированные заявки"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = request.data.get('status')
        if new_status not in [Dish.COMPLETED, Dish.REJECTED]:
            return Response(
                {"detail": "Недопустимый статус"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем статус, модератора и дату завершения
        dish.status = new_status
        dish.moderator = request.user
        dish.completed_at = timezone.now()

        # Дополнительные расчеты при завершении
        if new_status == Dish.COMPLETED:
            # Пример расчета дополнительных полей
            dish.total_sum = sum(
                os.service.price for os in dish.orderservices.all()
            )

        dish.save()

        return Response(DishSerializer(dish).data)
