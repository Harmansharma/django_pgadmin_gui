# dashboard/utils.py

from django.db import connection

def get_all_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        return [row[0] for row in cursor.fetchall()]

def get_all_tables_with_columns():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        table_columns = {}
        for table in tables:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s", [table])
            cols = [row[0] for row in cursor.fetchall()]
            table_columns[table] = cols
        return table_columns

