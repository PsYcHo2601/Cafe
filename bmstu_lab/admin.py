from django.contrib import admin
from .models import Product

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'id')  # Поля, которые будут отображаться в списке товаров
    search_fields = ('name', 'id')  # Поля, по которым можно будет осуществлять поиск
    list_filter = ('price',)  # Фильтры для списка товаров

admin.site.register(Product, ProductAdmin)
