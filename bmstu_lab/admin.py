from django.contrib import admin
from django.utils.html import format_html

from .models import Product, AuthUser, Services, OrderServices, Orders


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'id')  # Поля, которые будут отображаться в списке товаров
    search_fields = ('name', 'id')  # Поля, по которым можно будет осуществлять поиск
    list_filter = ('price',)  # Фильтры для списка товаров

@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ('login', 'is_staff')
    list_filter = ('is_staff', )
    search_fields = ('login',)
    ordering = ('login',)

@admin.register(Services)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'image_preview')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('image_preview',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Изображение', {
            'fields': ('image_url',),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image_url:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.image_url)
        return "-"
    image_preview.short_description = "Превью"

class OrderServiceInline(admin.TabularInline):
    model = OrderServices
    extra = 1
    raw_id_fields = ('service',)


@admin.register(Orders)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'creator__login', 'created_at', 'total_amount_display')
    list_filter = ('status', 'created_at', 'moderator__login')
    search_fields = ('creator__login', 'id')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('status', 'creator')
        }),
        ('Даты', {
            'fields': ('created_at', 'formed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Модерация', {
            'fields': ('moderator', 'total_amount'),
            'classes': ('collapse',)
        }),
    )
    inlines = [OrderServiceInline]
    actions = ['calculate_total']

    def total_amount_display(self, obj):
        if obj.total_amount:
            return f"{obj.total_amount} руб."
        return "-"
    total_amount_display.short_description = "Сумма"

    def calculate_total(self, request, queryset):
        for order in queryset:
            order.calculate_total()
        self.message_user(request, "Суммы пересчитаны")
    calculate_total.short_description = "Пересчитать сумму"

@admin.register(OrderServices)
class OrderServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'service', 'quantity', 'is_main')
    list_filter = ('is_main', 'service')
    raw_id_fields = ('order', 'service')
    search_fields = ('order__id', 'service__name')

    autocomplete_fields = ['order', 'service']

    fieldsets = (
        (None, {
            'fields': ('order', 'service', 'quantity', 'is_main', 'order_number')
        }),
    )

admin.site.register(Product, ProductAdmin)
