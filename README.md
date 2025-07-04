#  PostgreSQL Admin Dashboard (Django + Bootstrap)

This project is a web-based GUI built with Django that lets you interact with a PostgreSQL database just like pgAdmin.

---

##  Features

-  Dashboard showing tables: **Customers**, **Orders**, **Sales**
-  Full **CRUD operations** for each table
-  Custom **SQL Query Runner** at the bottom of every page
-  **Pagination** for large datasets
-  Bootstrap 5-based responsive UI
-  User-friendly alerts and error handling

---

##  Tech Stack

- Python 3.12.11
- Django (5.2.3)
- PostgreSQL(16.2)
- Bootstrap 5
- HTML5 / CSS3

---

## Project Setup

## 1. Clone the repository

```bash
git clone https://github.com/Harmansharma/django_pgadmin_gui.git
cd django_pgadmin_gui.git

## 2. Create & Activate a Virtual Environment

python -m venv venv
source venv/bin/activate  # For Linux

## 3. Install Requirements
   
pip install -r requirements.txt

## 4. Set Up PostgreSQL

Create a PostgreSQL database named postgres_gui_db

Update settings.py with:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres_gui_db',
        'USER': 'your_pg_user',
        'PASSWORD': 'your_pg_password',
        'HOST': 'localhost',
        'PORT': '5433', # Depend upon version
    }
}

## 5. Run Migrations
python manage.py makemigrations
python manage.py migrate


## 6. Dummy Data
To create dummy data:

python manage.py shell

from dashboard.models import Customer, Order, Sales
from datetime import date
c1 = Customer.objects.create(name="Harman", email="harman@gmail.com", phone="9123456789")
o1 = Order.objects.create(customer=c1, product_name="Laptop", quantity=1, order_date=date.today())
Sales.objects.create(order=o1, total_amount=50000, payment_status="paid")
exit()

## 7. Run Server
python manage.py runserver

## 8. Run on Browser
Visit: http://localhost:8000

