from django.db import models
from django.core.validators import RegexValidator, EmailValidator

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator(message="Enter a valid email")])
    phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', message="Phone number must be in the format: +91XXXXXXXXXX")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    order_date = models.DateField()

    class Meta:
        db_table = 'orders'

    def __str__(self):
        return f"Order of {self.product_name} ({self.quantity})"

class Sales(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed')
    ])
    sale_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sales'

    def __str__(self):
        return f"Sale for {self.order}"