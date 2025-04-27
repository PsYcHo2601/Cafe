from django.db import models
from drf_yasg.utils import swagger_auto_schema
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import permission_classes, authentication_classes, api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from .models import Dish, Services, OrderServices, CustomUser, AuthUser
from .permissions import IsAdmin, IsManager
from .serializers import (
    ServicesSerializer,
    DishSerializer,
    CreateDishSerializer,
    UpdateDishStatusSerializer,
    ServicesListSerializer,
    DishListSerializer, UserSerializer
)
from django.conf import settings
import uuid
import io

MINIO_URL = "http://localhost:9000/cafe"

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt

import redis

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

# создаем инстанс и указываем координаты БД на локальной машине
r = redis.Redis(
    host='127.0.0.1',
    port='6379')

r.set('somekey', '1000-7')  # сохраняем ключ 'somekey' с значением '1000-7!'
value = r.get('somekey')  # получаем значение по ключу

for key in session_storage.scan_iter('*'):
    if r.type(key).decode() == 'string':
        value = r.get(key)
        print(f"Ключ: {key}, Значение: {value}")


@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
def login_view(request):
    username = request.data["email"]
    password = request.data["password"]
    user = authenticate(request, email=username, password=password)
    if user is not None:
        random_key = uuid.uuid4()
        session_storage.set(str(random_key), username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", str(random_key))

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")


def logout_view(request):
    logout(request._request)
    return Response({'status': 'Success'})


class UserViewSet(viewsets.ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ['post']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def method_permission_classes(classes):
        def decorator(func):
            def decorated_func(self, *args, **kwargs):
                self.permission_classes = classes
                self.check_permissions(self.request)
                return func(self, *args, **kwargs)

            return decorated_func

        return decorator

    model_class = CustomUser

    def post(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(email=request.data['email']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(email=serializer.data['email'],
                                                 password=serializer.data['password'],
                                                 is_superuser=serializer.data['is_superuser'],
                                                 is_staff=serializer.data['is_staff'])
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ServicesListView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.COOKIES.get('session_id')

        if not session_id or not session_storage.get(session_id):
            return Response({'error': 'Invalid session'}, status=401)

        # Фильтрация услуг
        services = Services.objects.filter(is_active=True)

        # Получаем черновик заявки пользователя
        user_draft = Dish.objects.filter(
            creator_id=request.user.id,
            status=Dish.DRAFT
        ).first()

        # Аннотируем количество услуг в заявке
        if user_draft:
            services = services.annotate(
                in_draft_count=Count(
                    'orderservices',
                    filter=models.Q(orderservices__order=user_draft)
                ))
        else:
            services = services.annotate(in_draft_count=models.Value(0, output_field=models.IntegerField()))

        serializer = ServicesListSerializer(services, many=True, context={
            'draft_id': user_draft.id if user_draft else None})
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ServicesSerializer)
    def post(self, request):
        serializer = ServicesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServicesDetailView(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['get']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def method_permission_classes(classes):
        def decorator(func):
            def decorated_func(self, *args, **kwargs):
                self.permission_classes = classes
                self.check_permissions(self.request)
                return func(self, *args, **kwargs)

            return decorated_func

        return decorator

    def get(self, request, pk):
        service = get_object_or_404(Services, pk=pk, is_active=True)
        serializer = ServicesSerializer(service)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ServicesSerializer)
    def put(self, request, pk):
        service = get_object_or_404(Services, pk=pk)
        serializer = ServicesSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=ServicesSerializer)
    def delete(self, request, pk):
        service = get_object_or_404(Services, pk=pk)

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
        session_id = request.COOKIES.get('session_id')

        if not session_id or not session_storage.get(session_id):
            return Response({'error': 'Invalid session'}, status=401)
        user_name = session_storage.get(session_id).decode()
        user = CustomUser.objects.get(email=user_name)

        if not user.is_staff and not user.is_superuser:
            return Response({'error': 'Invalid authorization'}, status=401)
        if user.is_superuser:
            dishes = Dish.objects.all()
            serializer = DishListSerializer(dishes, many=True)
            return Response(serializer.data)

        dishes = Dish.objects.filter(creator_id=AuthUser.objects.get(login='staff').id)
        serializer = DishListSerializer(dishes, many=True)
        return Response(serializer.data)

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

        result = serializer.data
        for service in result['services']:
            service['coffee_number'] = service['order_number']
            del service['order_number']
            del service['is_main']

        return Response(result)

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

        session_id = request.COOKIES.get('session_id')

        if not session_id or not session_storage.get(session_id):
            return Response({'error': 'Invalid session'}, status=401)
        user_name = session_storage.get(session_id).decode()
        user = CustomUser.objects.get(email=user_name)

        if not user.is_staff and not user.is_superuser:
            return Response({'error': 'Invalid authorization'}, status=401)
        if user.is_superuser:
            return Response({'status': 'Success'}, status=200)

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
