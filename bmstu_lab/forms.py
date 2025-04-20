from django import forms
from django.forms import inlineformset_factory
from .models import Order, OrderItem, Product


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'table', 'waiter')


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    fields=('product', 'quantity', 'guest_name'),
    extra=1,
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        'guest_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя гостя (необязательно)'}),
    }
)
