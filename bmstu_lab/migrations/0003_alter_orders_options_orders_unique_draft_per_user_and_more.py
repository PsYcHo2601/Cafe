# Generated by Django 5.1.6 on 2025-03-24 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bmstu_lab', '0002_authuser_product_services_orders_orderservices'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orders',
            options={'verbose_name': 'Заявка', 'verbose_name_plural': 'Заявки'},
        ),
        migrations.AddConstraint(
            model_name='orders',
            constraint=models.UniqueConstraint(condition=models.Q(('status', 'draft')), fields=('creator',), name='unique_draft_per_user'),
        ),
        migrations.AlterModelTable(
            name='orders',
            table='orders',
        ),
    ]
