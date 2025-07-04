# forms.py
from django import forms
from .models import Customer, Order, Sales

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer', 'product_name', 'quantity', 'order_date']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'})
        }

class SalesForm(forms.ModelForm):
    class Meta:
        model = Sales
        fields = ['order', 'total_amount', 'payment_status']
