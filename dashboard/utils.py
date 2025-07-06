# dashboard/utils.py

from django.db import connection

def get_all_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        return [row[0] for row in cursor.fetchall()]
