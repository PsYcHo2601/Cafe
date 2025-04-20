from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название кофе")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена")
    is_available = models.BooleanField(default=True, verbose_name="Доступен для заказа")
    image = models.URLField(max_length=255, blank=True, null=True, verbose_name="URL изображения")

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        return '/static/images/coffee-placeholder.jpg'  # Запасное изображение

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"


class Table(models.Model):
    number = models.PositiveIntegerField(unique=True, verbose_name="Номер столика")
    is_active = models.BooleanField(default=True, verbose_name="Активен (доступен для заказов)")

    def __str__(self):
        return f"Столик №{self.number}"

    class Meta:
        verbose_name = "Столик"
        verbose_name_plural = "Столики"


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('preparing', 'Готовится'),
        ('ready', 'Готов'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    ]

    waiter = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Официант")
    table = models.ForeignKey(Table, on_delete=models.PROTECT, verbose_name="Столик")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return f"Заказ #{self.id} - {self.table} ({self.get_status_display()})"

    @property
    def total_sum(self):
        return sum(item.price * item.quantity for item in self.items.all())

    @property
    def sum_by_guest(self):
        # Возвращает суммы по именам гостей
        guests = {}
        for item in self.items.all():
            guest = item.guest_name or 'Общий'
            guests[guest] = guests.get(guest, 0) + (item.price * item.quantity)
        return guests

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        # Один активный заказ на столик
        constraints = [
            models.UniqueConstraint(
                fields=['table'],
                condition=models.Q(status__in=['new', 'preparing', 'ready']),
                name='unique_active_order_per_table'
            )
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Продукт")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    guest_name = models.CharField(max_length=100, blank=True, verbose_name="Имя гостя (для подписи)")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Цена на момент заказа")
    item_number = models.PositiveIntegerField(verbose_name="Номер позиции в заказе")

    def __str__(self):
        return f"{self.product.name} ({self.guest_name or 'без имени'}) - {self.order}"

    def save(self, *args, **kwargs):
        if not self.item_number:
            max_number = OrderItem.objects.filter(order=self.order).aggregate(models.Max('item_number'))[
                             'item_number__max'] or 0
            self.item_number = max_number + 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        # Уникальный номер позиции в рамках заказа
        unique_together = ('order', 'item_number')
