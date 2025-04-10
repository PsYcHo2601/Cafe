from datetime import datetime

from django.db.models import Q, Exists, OuterRef
from django.shortcuts import render
from bmstu_lab.models import Coffee, Services, Orders, OrderServices, AuthUser  # Убедись, что имя модели совпадает!
from django.shortcuts import render, get_object_or_404

MINIO_URL = "http://localhost:9000/cafe"


def get_basket():
    # todo будет доделано до нормального вида
    user_id = AuthUser.objects.all().order_by('login').first().id
    if Orders.objects.filter(creator_id=user_id, status=Orders.DRAFT).exists():
        basket = Orders.objects.get(creator_id=user_id, status=Orders.DRAFT)
    else:
        basket = Orders(creator_id=user_id, created_at=datetime.now(), status=Orders.DRAFT)
        basket.save()

    return basket


def coffee_list(request):
    """
    Перечень кофе (+поиск по наименованию, фильтрация по цене и дате)
    """
    search_query = request.GET.get("search", "").strip().lower()
    filter_by = request.GET.get("filter_by", "all")

    flt = Q()
    basket = get_basket()
    orders = OrderServices.objects.filter(order_id=basket.id)

    if search_query:
        flt &= Q(name__icontains=search_query)

    filtered_coffee = Services.objects.filter(flt).annotate(
        added_to_basket=Exists(orders.filter(service_id=OuterRef('pk'))))

    if filter_by == "price":
        filtered_coffee = filtered_coffee.order_by('price')
    elif filter_by == "date":
        filtered_coffee = filtered_coffee.order_by('-date')

    basket_count = orders.count()

    return render(request, "coffee_list.html",
                  {"coffee": filtered_coffee, "basket_count": basket_count, "search_query": search_query,
                   "filtered_by": filter_by})


def coffee_detail(request, coffee_id):
    """
    Информация о кофе
    :param coffee_id: идентификатор товара (кофе)
    """
    item = Services.objects.get(id=coffee_id)
    return render(request, "coffee_detail.html", {"coffee": item})


def basket_detail(request):
    """
    Содержимое корзины
    :return: перечень товаров добавленных в корзину
    """
    basket = get_basket()
    basket_services = OrderServices.objects.filter(order_id=basket.id).select_related('service')

    result = []
    for basket_service in basket_services:
        result.append(basket_service.service)

    # Страница корзины
    return render(request, "basket_detail.html", {"basket": result})


def add_to_basket(request, product_id):
    """
    Добавление в корзину
    :param product_id: идентификатор товара (кофе)
    """
    # Добавление товара в корзину через отдельный URL
    if request.method == "POST":
        product = Services.objects.filter(id=product_id).first()
        if product:
            basket = get_basket()
            OrderServices.objects.get_or_create(order_id=basket.id, service_id=product.id)  # Добавляем товар в корзину

            # Возвращаем пользователя обратно на страницу списка товаров
    return coffee_list(request)


def delete_from_backet(request, product_id):
    """
    Удаление из корзины
    :param product_id: идентификатор товара (кофе)
    """
    basket = get_basket()
    OrderServices.objects.filter(order_id=basket.id, service_id=product_id).delete()

    return basket_detail(request)


from django.shortcuts import render


def home(request):
    return render(request, "base.html", {"coffee": Services.objects.all()})  # Отображает base.htmllter(id=product
