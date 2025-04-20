from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .forms import OrderCreateForm, OrderItemFormSet
from .models import Product, Order, OrderItem, Table


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(is_available=True)


class TableListView(LoginRequiredMixin, ListView):
    model = Table
    template_name = 'table_list.html'
    context_object_name = 'tables'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем информацию о текущих заказах для каждого столика
        tables = context['tables']
        active_orders = Order.objects.filter(status__in=['new', 'preparing', 'ready'])
        table_order_map = {order.table_id: order for order in active_orders}

        for table in tables:
            table.current_order = table_order_map.get(table.id)

        return context


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'order_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table_id = self.kwargs.get('table_id')
        table = get_object_or_404(Table, id=table_id)

        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST)
        else:
            context['formset'] = OrderItemFormSet(queryset=OrderItem.objects.none())

        context['table'] = table
        context['products'] = Product.objects.filter(is_available=True)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        table_id = self.kwargs.get('table_id')
        table = get_object_or_404(Table, id=table_id)

        # Проверяем, что для столика нет активного заказа
        if Order.objects.filter(table=table, status__in=['new', 'preparing', 'ready']).exists():
            messages.error(self.request, 'Для этого столика уже есть активный заказ')
            return redirect('table_list')

        if formset.is_valid():
            order = form.save(commit=False)
            order.waiter = self.request.user
            order.table = table
            order.save()

            # Сохраняем позиции заказа
            instances = formset.save(commit=False)
            for instance in instances:
                instance.order = order
                instance.price = instance.product.price  # Сохраняем текущую цену
                instance.save()

            messages.success(self.request, 'Заказ успешно создан')
            return redirect('order_detail', pk=order.pk)

        return self.render_to_response(self.get_context_data(form=form))


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['items'] = order.items.all().order_by('item_number')

        # Группировка по гостям для отображения
        guests = {}
        for item in context['items']:
            guest_name = item.guest_name or 'Общий заказ'
            if guest_name not in guests:
                guests[guest_name] = []
            guests[guest_name].append(item)

        context['grouped_items'] = guests
        return context


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderCreateForm
    template_name = 'order_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST, instance=order)
        else:
            context['formset'] = OrderItemFormSet(instance=order)

        context['products'] = Product.objects.filter(is_available=True)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            self.object = form.save()
            instances = formset.save(commit=False)

            for instance in instances:
                instance.order = self.object
                if not instance.price:  # Если цена не установлена (новый товар)
                    instance.price = instance.product.price
                instance.save()

            # Удаление отмеченных позиций
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(self.request, 'Заказ успешно обновлен')
            return redirect('order_detail', pk=self.object.pk)

        return self.render_to_response(self.get_context_data(form=form))


class OrderStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order = get_object_or_404(Order, pk=kwargs['pk'])
        new_status = request.POST.get('status')

        if new_status in dict(Order.STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа изменен на "{order.get_status_display()}"')

        return redirect('order_detail', pk=order.pk)