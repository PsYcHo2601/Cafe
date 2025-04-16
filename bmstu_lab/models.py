import datetime
import uuid

from django.contrib.auth.models import AbstractUser, Permission, Group
from django.core.validators import MaxValueValidator
from django.db import models


class AuthUser(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False, null=False, unique=True)
    login = models.CharField(max_length=255, unique=True, null=False)
    password = models.CharField(max_length=255, unique=True, null=False)

    is_staff = models.BooleanField(null=False, default=False)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class Dish(models.Model):
    DRAFT = 'draft'
    DELETED = 'deleted'
    FORMED = 'formed'
    COMPLETED = 'completed'
    REJECTED = 'rejected'

    STATUS_CHOICES = [
        (DRAFT, 'Черновик'),
        (DELETED, 'Удален'),
        (FORMED, 'Сформирован'),
        (COMPLETED, 'Завершен'),
        (REJECTED, 'Отклонен'),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, null=False, db_column='id')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT, verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    creator = models.ForeignKey('AuthUser', on_delete=models.PROTECT, related_name='created_orders',
                                verbose_name="Создатель"
                                )
    formed_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата формирования")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата завершения")
    moderator = models.ForeignKey('AuthUser', on_delete=models.PROTECT, blank=True, null=True,
                                  related_name='moderated_orders',
                                  verbose_name="Модератор"
                                  )
    table_number = models.PositiveIntegerField(verbose_name="Номер стола", null=False, default=0,
                                               validators=[MaxValueValidator(10)],
                                               help_text="Номер стола не может превышать 10")
    total_sum = models.PositiveIntegerField(verbose_name="Сумма заказа", null=False, default=0)

    def __str__(self):
        return f"Заявка #{self.id} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        db_table = 'dish'
        constraints = [
            models.UniqueConstraint(
                fields=['creator'],
                condition=models.Q(status='draft'),
                name='unique_draft_per_user'
            )
        ]


class OrderServices(models.Model):
    order = models.ForeignKey(
        'Dish',
        on_delete=models.CASCADE,
        verbose_name="Заявка"
    )
    service = models.ForeignKey(
        'Services',
        on_delete=models.PROTECT,
        verbose_name="Услуга"
    )
    is_main = models.BooleanField(default=False, verbose_name="Основная услуга")
    order_number = models.PositiveIntegerField(verbose_name="Порядковый номер", default=1)
    guest_name = models.CharField(verbose_name='Имя гостя', max_length=255)

    def __str__(self):
        return f"{self.service.name} в заявке #{self.order.id}"

    class Meta:
        verbose_name = "Услуга в заявке"
        verbose_name_plural = "Услуги в заявках"
        db_table = 'order_services'
        unique_together = [('order', 'service')]


class Services(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название услуги")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    image_url = models.URLField(max_length=255, blank=True, null=True, verbose_name="URL изображения")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    date = models.DateField(default=datetime.date.today(), verbose_name='Дата')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        db_table = 'services'
