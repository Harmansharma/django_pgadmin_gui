from django.shortcuts import render
from django.db import connection

def home(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE';
        """)
        tables = [row[0] for row in cursor.fetchall()]
    
    return render(request, 'dashboard/home.html', {'tables': tables})
