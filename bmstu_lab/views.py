from datetime import datetime

from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.db import connection

MINIO_URL = "http://localhost:9000/cafe"

coffee = [
    {"id": 1, "name": "американо", "price": 229, "date": "2025-04-10",
     "description": "Кофе американо.",
     "image_url": "http://localhost:9000/cafe/americano.png"},
    {"id": 2, "name": "Латте", "price": 299, "date": "2025-04-12",
     "description": "Кофе латте.",
     "image_url": "http://localhost:9000/cafe/latte.png"},
    {"id": 3, "name": "Флэт-уайт", "price": 299, "date": "2025-04-15",
     "description": "Кофе Флэт-уайт.",
     "image_url": "http://localhost:9000/cafe/flatwhite.png"},
    {"id": 4, "name": "Венский кофе", "price": 349, "date": "2025-04-15",
     "description": "Венский кофе",
     "image_url": "http://localhost:9000/cafe/viennesecoffee.png"},
    {"id": 5, "name": "Горячий шоколад", "price": 349, "date": "2025-04-20",
     "description": "Горячий шоколад.",
     "image_url": "http://localhost:9000/cafe/hotchokolate.png"},
    {"id": 6, "name": "Капучино", "price": 319, "date": "2025-04-20",
     "description": "Капучино.",
     "image_url": "http://localhost:9000/cafe/capuccino.png"}
]

orders = {'1': {"id": 1, "name": "американо", "price": 229, "date": "2025-04-10",
                "description": "Кофе американо.",
                "image_url": "http://localhost:9000/cafe/americano.png"}}


def get_orders():
    return orders


def coffee_list(request):
    """
    Перечень кофе (+поиск по наименованию, фильтрация по цене и дате)
    """
    search_query = request.GET.get("search", "").strip().lower()
    filter_by = request.GET.get("filter_by", "all")

    filtered_coffee = coffee.copy()

    # Apply search filter
    if search_query:
        filtered_coffee = [item for item in filtered_coffee
                           if search_query in item['name'].lower()]

    orders_items = orders.keys()
    for item in filtered_coffee:
        item['added_to_orders'] = str(item['id']) in orders_items

    # Apply sorting
    if filter_by == "price":
        filtered_coffee.sort(key=lambda x: x['price'])
    elif filter_by == "date":
        filtered_coffee.sort(key=lambda x: x['date'], reverse=True)

    orders_count = len(orders)

    return render(request, "coffee_list.html",
                  {"coffee": filtered_coffee, "orders_count": orders_count,
                   "search_query": search_query, "filtered_by": filter_by})


def coffee_detail(request, coffee_id):
    """
    Информация о кофе
    :param coffee_id: идентификатор товара (кофе)
    """
    item = next((item for item in coffee if item['id'] == int(coffee_id)), None)
    if not item:
        raise Http404("Ошибка. Кофе не найдено.")
    return render(request, "coffee_detail.html", {"coffee": item})


def orders_detail(request):
    """
    Содержимое корзины
    :return: перечень товаров добавленных в корзину
    """
    orders_items = orders.values()
    return render(request, "orders_detail.html", {"orders": orders_items})


def add_to_orders(request, product_id):
    """
    Добавление в корзину
    :param product_id: идентификатор товара (кофе)
    """
    if request.method == "POST":
        product = next((item for item in coffee if item['id'] == product_id), None)
        if product:
            orders[str(product_id)] = product
    return coffee_list(request)


def delete_from_orders(request, product_id):
    """
    Удаление из корзины
    :param product_id: идентификатор товара (кофе)
    """
    if str(product_id) in orders.keys():
        del orders[str(product_id)]
    return orders_detail(request)


def home(request):
    return render(request, "base.html", {"coffee": coffee})
