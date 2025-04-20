from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order, OrderItem, Table


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity', 'guest_name', 'price', 'item_number', 'total_price')
    readonly_fields = ('price', 'total_price')

    def total_price(self, obj):
        return obj.price * obj.quantity

    total_price.short_description = 'Сумма'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table_number', 'waiter_info', 'status', 'created_at', 'total_sum')
    list_filter = ('status', 'created_at', 'waiter')
    search_fields = ('table__number', 'waiter__username')
    inlines = (OrderItemInline,)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_completed']

    fieldsets = (
        (None, {
            'fields': ('table', 'waiter', 'status')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def table_number(self, obj):
        return f"№{obj.table.number}"

    table_number.short_description = 'Столик'

    def waiter_info(self, obj):
        return obj.waiter.get_full_name() or obj.waiter.username

    waiter_info.short_description = 'Официант'

    def total_sum(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())

    total_sum.short_description = 'Сумма заказа'

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')

    mark_as_completed.short_description = "Пометить как завершенные"


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'is_active', 'current_order_link')
    list_filter = ('is_active',)
    list_editable = ('is_active',)

    def current_order_link(self, obj):
        order = Order.objects.filter(table=obj, status__in=['new', 'preparing', 'ready']).first()
        if order:
            return format_html('<a href="{}">Заказ #{}</a>',
                               f'/admin/coffee/order/{order.id}/change/',
                               order.id)
        return "-"

    current_order_link.short_description = 'Текущий заказ'


# Отдельная регистрация OrderItem если нужен отдельный доступ
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'product', 'quantity', 'guest_name', 'price', 'total_price')
    list_filter = ('product',)
    search_fields = ('order__id', 'guest_name')

    def order_link(self, obj):
        return format_html('<a href="{}">Заказ #{}</a>',
                           f'/admin/coffee/order/{obj.order.id}/change/',
                           obj.order.id)

    order_link.short_description = 'Заказ'

    def total_price(self, obj):
        return obj.price * obj.quantity

    total_price.short_description = 'Сумма'