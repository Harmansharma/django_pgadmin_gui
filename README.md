#  PostgreSQL Admin Dashboard (Django + Bootstrap)

This project is a web-based GUI built with Django that lets you interact with a PostgreSQL database just like pgAdmin.

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


## 6. Run Server
python manage.py runserver

## 7. Run on Browser
Visit: http://localhost:8000


##  Features

1. Dashboard
Sidebar listing all tables in the database

Create, edit, view, and delete tables

2. Table Operations
Create tables with dynamic fields, constraints, defaults, and indexes

Edit table schema: rename/add/drop columns, change data types, add foreign keys or indexes

Drop tables with FK dependency checks

3. Row Operations
Insert rows with created_at and updated_at auto-managed

Edit rows with intelligent form binding and field validation

Delete rows using primary key resolution

Show row details with all related FK data (recursive traversal)

4. SQL Features
Run custom SQL queries using an embedded SQL editor

Live preview and result display for SQL outputs

5. Validations
Built-in checks for:

Reserved keyword restrictions (select, from, table, etc.)
Duplicate/invalid column names
Foreign key format validation eg.(employers(id))

---

##View                               Description

a)create_table_view--                Dynamically creates tables using form data
b)edit_table_view                    Edits existing table schema
c)drop_table_view                    Drops tables safely with FK check
d)dynamic_table_sql_crud             Displays table rows and adds new data
e)dynamic_edit_row                   Edits a single row in a table
f)delete_row                         Deletes a record using PK
g)dynamic_show_row                   Shows full record with related data
h)sql_editor                         Run and preview raw SQL queries
i)dashboard_home                     Shows all tables in sidebar and main view
j)fetch_related_data                 Recursively fetches child records from FK relationships