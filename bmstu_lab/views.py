from django.shortcuts import render

MINIO_URL = ""

coffee = [
    {"id": 1, "name": "Americano", "price": 229, "date": "2025-04-10",
     "description": "Кофе американо.",
     "image_url": ".png"},
    {"id": 2, "name": "Latte", "price": 299, "date": "2025-04-12",
     "description": "Кофе латте.",
     "image_url": ".png"},
    {"id": 3, "name": "Flat White", "price": 299, "date": "2025-04-15",
     "description": "Кофе  Флэт-уайт.",
     "image_url": ".png"},
    {"id": 4, "name": "Viennese Coffee", "price":349, "date": "2025-04-15",
     "description": "Венский кофе",
     "image_url": ".png"},
    {"id": 5, "name": "Hot Chocolate", "price": 349, "date": "2025-04-20",
     "description": "Горячий шоколад.",
     "image_url": ".png"},
    {"id": 6, "name": "Capuccino", "price": 319, "date": "2025-04-20",
     "description": "Капучино.",
     "image_url": ".png"}
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
    return render(request, "1.html", {"coffee": filtered_coffee, "basket_count": len(basket), "search_query": search_query, "filtered_by": filter_by })


def coffee_detail(request, coffee_id):
    #Страница с подробной информацией о товаре
    item = next((c for c in coffee if c["id"] == coffee_id), None)
    return render(request, "3.html", {"coffee": item})


def basket_detail(request):
    #Страница корзины
    return render(request, "3.html", {"basket": basket})


def add_to_basket(request, product_id):
    #Добавление товара в корзину через отдельный URL
    global basket
    if request.method == "POST":
        product = next((c for c in coffee if c["id"] == product_id), None)
        if product:
            basket[product_id] = product  # Добавляем товар в корзину

    # Возвращаем пользователя обратно на страницу списка товаров
    return coffee_list(request)