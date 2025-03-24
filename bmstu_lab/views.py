from django.shortcuts import render
from bmstu_lab.models import Coffee  # Убедись, что имя модели совпадает!
from django.shortcuts import render, get_object_or_404

MINIO_URL = "http://localhost:9000/cafe"

coffee = [
    {"id": 1, "name": "Americano", "price": 229, "date": "2025-04-10",
     "description": "Кофе американо.",
     "image_url": "http://localhost:9000/cafe/americano.png"},
    {"id": 2, "name": "Latte", "price": 299, "date": "2025-04-12",
     "description": "Кофе латте.",
     "image_url": "http://localhost:9000/cafe/latte.png"},
    {"id": 3, "name": "Flat White", "price": 299, "date": "2025-04-15",
     "description": "Кофе  Флэт-уайт.",
     "image_url": "http://localhost:9000/cafe/flatwhite.png"},
    {"id": 4, "name": "Viennese Coffee", "price":349, "date": "2025-04-15",
     "description": "Венский кофе",
     "image_url": "http://localhost:9000/cafe/viennesecoffee.png"},
    {"id": 5, "name": "Hot Chocolate", "price": 349, "date": "2025-04-20",
     "description": "Горячий шоколад.",
     "image_url": "http://localhost:9000/cafe/hotchokolate.png"},
    {"id": 6, "name": "Capuccino", "price": 319, "date": "2025-04-20",
     "description": "Капучино.",
     "image_url": "http://localhost:9000/cafe/capuccino.png"}
]
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
    coffee = get_object_or_404(Coffee, id=coffee_id)
    return render(request, "coffee_detail.html", {"coffee": coffee})

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