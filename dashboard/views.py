# views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer, Order, Sales
from .forms import CustomerForm, OrderForm, SalesForm
from django.db import connection, DatabaseError
from django.contrib import messages
from django.core.paginator import Paginator

# Customer Views
def run_sql_query(request):
    if 'clear_query' in request.POST:
        request.session['sql_query'] = ''
        return '', [], [], None
    
    sql_query = request.POST.get('sql_query', '')
    request.session['sql_query'] = sql_query
    columns = []
    result = []
    error = None  

    if sql_query:
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchall()
        except DatabaseError as e:
            error = str(e)

    return sql_query, columns, result, error


# ========== Customer Views ==========
def customer_list(request):
    customers = Customer.objects.all().order_by('-id')
    paginator = Paginator(customers, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        sql_query, columns, result, error = run_sql_query(request)
    else:
        sql_query = request.session.get('sql_query', '')
        columns = []
        result = []
        error = None

    return render(request, 'dashboard/customer_list.html', {
        'page_obj': page_obj,
        'sql_query': sql_query,
        'columns': columns,
        'result': result,
        'error': error,
        'show_query_box': True
    })

def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Add Customer'})

def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Edit Customer'})

def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    messages.success(request, "Customer deleted successfully.")
    return redirect('customer_list')

# ========== Order Views ==========
def order_list(request):
    orders = Order.objects.select_related('customer').all().order_by('-id')
    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        sql_query, columns, result, error = run_sql_query(request)
    else:
        sql_query = request.session.get('sql_query', '')
        columns = []
        result = []
        error = None

    return render(request, 'dashboard/order_list.html', {
        'page_obj': page_obj,
        'sql_query': sql_query,
        'columns': columns,
        'result': result,
        'error': error,
        'show_query_box': True
    })


def order_create(request):
    form = OrderForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('order_list')
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Add Order'})

def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    form = OrderForm(request.POST or None, instance=order)
    if form.is_valid():
        form.save()
        return redirect('order_list')
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Edit Order'})

def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, "Order deleted successfully.")
    return redirect('order_list')

# ========== Sales Views ==========
def sales_list(request):
    sales = Sales.objects.select_related('order__customer').all().order_by('-id')
    paginator = Paginator(sales, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        sql_query, columns, result, error = run_sql_query(request)
    else:
        sql_query = request.session.get('sql_query', '')
        columns = []
        result = []
        error = None

    return render(request, 'dashboard/sales_list.html', {
        'page_obj': page_obj,
        'sql_query': sql_query,
        'columns': columns,
        'result': result,
        'error': error,
        'show_query_box': True
    })

def sales_create(request):
    form = SalesForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('sales_list')
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Add Sale'})

def sales_edit(request, pk):
    sale = get_object_or_404(Sales, pk=pk)
    form = SalesForm(request.POST or None, instance=sale)
    if form.is_valid():
        form.save()
        return redirect('sales_list')
    return render(request, 'dashboard/form.html', {'form': form, 'title': 'Edit Sale'})

def sales_delete(request, pk):
    sale = get_object_or_404(Sales, pk=pk)
    sale.delete()
    messages.success(request, "Sale deleted successfully.")
    return redirect('sales_list')