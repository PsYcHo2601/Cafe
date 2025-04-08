from django.shortcuts import render
from bmstu_lab.models import Coffee  # Убедись, что имя модели совпадает!
from django.shortcuts import render, get_object_or_404

MINIO_URL = "http://localhost:9000/cafe"

coffee = []
# корзина
basket = {}

def coffee_list(request):
    search_query = request.GET.get("search","").strip().lower()
    filter_by = request.GET.get("filter_by","all")

    filtered_coffee = coffee
    if search_query:
        filtered_coffee = [c for c in coffee if search_query in c["name"].lower() or search_query in str(c["price"]) or search_query in c["date"]]

    if filter_by == "price":
        filtered_coffee = sorted(filtered_coffee, key=lambda x: x["price"])
    elif filter_by == "date":
        filtered_coffee = sorted(filtered_coffee, key=lambda x: x["date"])
    return render(request, "coffee_list.html", {"coffee": filtered_coffee, "basket_count": len(basket), "search_query": search_query, "filtered_by": filter_by})


def coffee_detail(request, coffee_id):
    item = next((c for c in coffee if c["id"] == coffee_id), None)
    return render(request, "coffee_detail.html", {"clothes": item})

def basket_detail(request):
    #Страница корзины
    return render(request, "basket_detail.html", {"basket": basket})


def add_to_basket(request, product_id):
    #Добавление товара в корзину через отдельный URL
    global basket
    if request.method == "POST":
        product = next((c for c in coffee if c["id"] == product_id), None)
        if product:
            basket[product_id] = product  # Добавляем товар в корзину

    # Возвращаем пользователя обратно на страницу списка товаров
    return coffee_list(request)

from django.shortcuts import render

def home(request):
    return render(request, "base.html", {"coffee":coffee})  # Отображает base.html

from django.shortcuts import render
from django.db.models import Q  # Не забудь импортировать Q
from .models import Coffee  # Убедись, что у тебя есть модель Coffee

def search_results(request):
    query = request.GET.get("q", "").strip()
    results = Coffee.objects.all()  # По умолчанию все товары

    if query:
        results = Coffee.objects.filter(
            Q(name__icontains=query) |  # Поиск по названию кофе
            Q(description__icontains=query) |  # Поиск по описанию
            Q(price__icontains=query)  # Поиск по цене
        )

    return render(request, "search_results.html", {"query": query, "results": results})