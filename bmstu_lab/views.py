from datetime import datetime

from django.db.models import Q

from bmstu_lab.models import Services, Dish, OrderServices, AuthUser  # Убедись, что имя модели совпадает!

MINIO_URL = "http://localhost:9000/cafe"


def get_dish():
    # todo будет доделано до нормального вида
    user_id = AuthUser.objects.all().order_by('login').first().id
    if Dish.objects.filter(creator_id=user_id, status=Dish.DRAFT).exists():
        dish = Dish.objects.get(creator_id=user_id, status=Dish.DRAFT)
    else:
        dish = Dish(creator_id=user_id, created_at=datetime.now(), status=Dish.DRAFT)
        dish.save()

    return dish


def coffee_list(request):
    """
    Перечень кофе (+поиск по наименованию, фильтрация по цене и дате)
    """
    search_query = request.GET.get("search", "").strip().lower()
    filter_by = request.GET.get("filter_by", "all")

    flt = Q()
    dish = get_dish()
    orders = OrderServices.objects.filter(order_id=dish.id)

    if search_query:
        flt &= Q(name__icontains=search_query)

    filtered_coffee = Services.objects.filter(flt)

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


def dish_detail(request):
    """
    Содержимое корзины
    :return: перечень товаров добавленных в корзину
    """
    dish = get_dish()
    dish_services = OrderServices.objects.filter(order_id=dish.id).select_related('service')

    result = []
    total_sum = 0
    for dish_service in dish_services:
        result.append(dish_service.service)
        total_sum += dish_service.service.price

    # Страница корзины
    return render(request, "basket_detail.html", {"basket": result, "total_sum": total_sum})


def add_to_dish(request, product_id):
    """
    Добавление в корзину
    :param product_id: идентификатор товара (кофе)
    """
    # Добавление товара в корзину через отдельный URL
    if request.method == "POST":
        product = Services.objects.filter(id=product_id).first()
        if product:
            dish = get_dish()
            OrderServices.objects.create(order_id=dish.id, service_id=product.id)

            # Возвращаем пользователя обратно на страницу списка товаров
    return coffee_list(request)


def update_coffee_guest_in_dish(request, order_service_id, guest_name):
    OrderServices.objects.filter(id=order_service_id).update(guest_name=guest_name)

    return dish_detail(request)


def update_dish_table(request, table_number):
    dish = get_dish()

    dish.table_number = table_number
    dish.save()

    return dish_detail(request)


def delete_from_dish(request, product_id):
    """
    Удаление из корзины
    :param product_id: идентификатор товара (кофе)
    """
    dish = get_dish()
    OrderServices.objects.filter(order_id=dish.id, service_id=product_id).delete()

    return dish_detail(request)


def set_dish_to_formed(request):
    dish = get_dish()
    dish.status = dish.FORMED

    dish_services = OrderServices.objects.filter(order_id=dish.id).select_related('service')

    total_sum = 0
    for dish_service in dish_services:
        total_sum += dish_service.service.price

    dish.total_sum = total_sum
    dish.save()

    return dish_detail(request)


from django.shortcuts import render


def home(request):
    return render(request, "base.html", {"coffee": Services.objects.all()})  # Отображает base.htmllter(id=product
