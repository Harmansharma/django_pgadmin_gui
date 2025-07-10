from django.shortcuts import render, redirect
from django.apps import apps
from django.forms import modelform_factory
from django.db import connection, DatabaseError
from django.http import Http404
from django.contrib import messages
from .utils import get_all_tables 
from .sql_runner import run_sql_query 




def home_redirect(request):
    tables = get_all_tables()
    if tables:
        return redirect('dynamic_table_sql_crud', table_name=tables[0])
    return render(request, 'dashboard/empty.html', {'message': 'No tables found in the database.'})

def dashboard_home(request):
    tables = get_all_tables()  # You already use this for sidebar

    return render(request, 'dashboard/dashboard_home.html', {
        'tables': tables
    })


def dashboard_view(request):
    tables = get_all_tables()
    return render(request, 'dashboard/dashboard_home.html', {'tables': tables})


def get_all_tables():
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        return [row[0] for row in cursor.fetchall()]
def dynamic_table_sql_crud(request, table_name):
    tables = get_all_tables()
    columns = []
    rows = []
    error = None

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 50")
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
    except DatabaseError as e:
        error = str(e)

    if request.method == 'POST' and 'add_row' in request.POST:
        set_default_created_at(table_name)

        # Step 1: Detect primary key column (auto-incremented)
        pk_column = get_primary_key_column(table_name)

        # Step 2: Define common auto-managed fields
        auto_fields = ['id', 'created_at', 'updated_at']

        values = []
        placeholders = []
        insert_columns = []

        for col in columns:
            if col.lower() in auto_fields or col == pk_column:
                continue
            val = request.POST.get(col, '').strip()
            if val == '':
                val = None  # Treat empty string as NULL
            insert_columns.append(col)
            placeholders.append('%s')
            values.append(val)

        if insert_columns:
            insert_sql = f"""
                INSERT INTO {table_name} ({', '.join(insert_columns)}, updated_at)
                VALUES ({', '.join(placeholders)}, CURRENT_TIMESTAMP AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata')
            """
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET TIME ZONE 'Asia/Kolkata';")  # ✅ Set IST
                    cursor.execute(insert_sql, values)
                    messages.success(request, "Row inserted successfully.")
                    return redirect('dynamic_table_sql_crud', table_name=table_name)
            except DatabaseError as e:
                error = str(e)

    return render(request, 'dashboard/dynamic_table_sql_crud.html', {
        'table_name': table_name,
        'columns': columns,
        'rows': rows,
        'tables': tables,
        'error': error,
    })

def get_primary_key_column(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
              AND tc.table_name = %s
            LIMIT 1;
        """, [table_name])
        row = cursor.fetchone()
        return row[0] if row else None

def delete_row(request, table_name, pk_value):
    pk_column = get_primary_key_column(table_name)
    if not pk_column:
        messages.error(request, "Cannot delete: No primary key found.")
        return redirect('dynamic_table_sql_crud', table_name=table_name)

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name} WHERE {pk_column} = %s", [pk_value])
            messages.success(request, "Row deleted successfully.")
    except Exception as e:
        messages.error(request, f"Delete failed: {e}")

    return redirect('dynamic_table_sql_crud', table_name=table_name)


def dynamic_edit_row(request, table_name, pk):
    columns = []
    row_data = {}
    pk_column = get_primary_key_column(table_name)
    error = None

    # Fetch existing row
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_column} = %s", [pk])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                row_data = dict(zip(columns, row))
    except DatabaseError as e:
        error = str(e)

    # Update on POST
    if request.method == 'POST':
        update_cols = []
        values = []
        auto_fields = ['id', 'created_at']

        for col in columns:
            if col in auto_fields or col == pk_column:
                continue  # Skip non-editable fields

            if col == 'updated_at':
                update_cols.append(f"{col} = CURRENT_TIMESTAMP AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata'")
            else:
                update_cols.append(f"{col} = %s")
                values.append(request.POST.get(col, '').strip())

        # Add PK for WHERE clause
        values.append(pk)

        update_sql = f"UPDATE {table_name} SET {', '.join(update_cols)} WHERE {pk_column} = %s"

        try:
            with connection.cursor() as cursor:
                cursor.execute("SET TIME ZONE 'Asia/Kolkata';")  # ✅ Set IST
                cursor.execute(update_sql, values)
                messages.success(request, "Row updated successfully.")
                return redirect('dynamic_table_sql_crud', table_name=table_name)
        except DatabaseError as e:
            error = str(e)

    return render(request, 'dashboard/dynamic_edit_row.html', {
        'table_name': table_name,
        'columns': columns,
        'row_data': row_data,
        'pk_column': pk_column,
        'error': error,
    })



def sql_editor(request):
    tables = get_all_tables()  # Reuse your existing sidebar
    sql_query, columns, result, error = run_sql_query(request)

    return render(request, 'dashboard/sql_editor.html', {
        'tables': tables,
        'sql_query': sql_query,
        'columns': columns,
        'result': result,
        'error': error,
    })

def set_default_created_at(table_name, column='created_at'):
    """
    Automatically sets the default CURRENT_TIMESTAMP on a given table's 'created_at' column.
    Only applies if the column exists and doesn't already have a default.
    """
    try:
        with connection.cursor() as cursor:
            # Check if column exists and is missing default
            cursor.execute(f"""
                SELECT column_name, column_default 
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, [table_name, column])
            row = cursor.fetchone()

            if row and row[1] is None:
                cursor.execute(f"""
                    ALTER TABLE {table_name}
                    ALTER COLUMN {column} SET DEFAULT CURRENT_TIMESTAMP
                """)
                print(f"[✅] Default timestamp set for {column} in table {table_name}")
            else:
                print(f"[ℹ️] Column {column} already has a default or does not exist.")

    except DatabaseError as e:
        print(f"[❌] Failed to set default on {table_name}.{column}: {str(e)}")

def create_table_view(request):
    error = None
    success = None
    generated_sql = None

    if request.method == 'POST':
        table_name = request.POST.get('table_name', '').strip()
        columns = request.POST.getlist('column_name[]')
        data_types = request.POST.getlist('data_type[]')
        not_nulls = request.POST.getlist('not_null[]')
        uniques = request.POST.getlist('unique[]')
        defaults = request.POST.getlist('default_value[]')
        is_fk = request.POST.getlist('is_foreign[]')
        ref_tables = request.POST.getlist('ref_table[]')
        ref_columns = request.POST.getlist('ref_column[]')
        pk_columns = request.POST.getlist('primary_key[]')

        column_defs = []
        fk_defs = []

        for i in range(len(columns)):
            try:
                name = columns[i].strip()
                dtype = data_types[i].strip()
            except IndexError:
                continue  # Skip incomplete definitions

            if not name or not dtype:
                continue

            col_def = f"{name} {dtype}"
            if i < len(not_nulls) and not_nulls[i] == 'on':
                col_def += " NOT NULL"
            if i < len(uniques) and uniques[i] == 'on':
                col_def += " UNIQUE"
            if i < len(defaults) and defaults[i]:
                col_def += f" DEFAULT {defaults[i]}"

            column_defs.append(col_def)

            if (
                i < len(is_fk)
                and is_fk[i] == 'on'
                and i < len(ref_tables)
                and i < len(ref_columns)
                and ref_tables[i] and ref_columns[i]
            ):
                fk_defs.append(f"FOREIGN KEY ({name}) REFERENCES {ref_tables[i]}({ref_columns[i]})")

        if pk_columns:
            column_defs.append(f"PRIMARY KEY ({', '.join(pk_columns)})")

        column_defs.extend(fk_defs)
        generated_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(column_defs) + "\n);"

        if 'preview_sql' in request.POST:
            return render(request, 'dashboard/create_table.html', {
                'generated_sql': generated_sql,
                'form_data': request.POST
            })

        try:
            with connection.cursor() as cursor:
                cursor.execute(generated_sql)
            success = f"✅ Table '{table_name}' created successfully!"
        except DatabaseError as e:
            error = str(e)

    return render(request, 'dashboard/create_table.html', {
        'error': error,
        'success': success,
        'generated_sql': generated_sql,
    })

    def add_updated_at_to_all_tables():
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table}
                        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    """)
                    print(f"✅ Added updated_at to {table}")
                except Exception as e:
                    print(f"❌ Failed on {table}: {e}")


def fetch_related_data(table_name, pk_value, depth=0, visited=None):
    if visited is None:
        visited = set()
    if (table_name, pk_value) in visited:
        return {}  # Prevent circular joins
    visited.add((table_name, pk_value))

    related_data = {}

    with connection.cursor() as cursor:
        # Find related tables (foreign keys where this table is the referenced table)
        fk_query = """
            SELECT tc.table_name, kcu.column_name, ccu.column_name
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu 
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu 
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND ccu.table_name = %s
        """
        cursor.execute(fk_query, [table_name])
        fks = cursor.fetchall()

        for child_table, child_fk_col, parent_pk_col in fks:
            try:
                cursor.execute(f"""
                    SELECT * FROM {child_table} WHERE {child_fk_col} = %s
                """, [pk_value])
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                child_rows = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    nested = fetch_related_data(child_table, row_dict['id'], depth+1, visited)
                    child_rows.append({
                        'data': row_dict,
                        'related': nested
                    })

                if child_rows:
                    related_data[child_table] = {
                        'columns': columns,
                        'rows': child_rows
                    }

            except Exception as e:
                continue

    return related_data



def dynamic_show_row(request, table_name, pk):
    pk_column = get_primary_key_column(table_name)
    row_data = {}
    columns = []
    nested_related = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_column} = %s", [pk])
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if row:
                row_data = dict(zip(columns, row))

        nested_related = fetch_related_data(table_name, pk)

    except DatabaseError as e:
        return render(request, 'dashboard/dynamic_show_row.html', {
            'table_name': table_name,
            'error': str(e),
        })

    return render(request, 'dashboard/dynamic_show_row.html', {
        'table_name': table_name,
        'row_data': row_data,
        'columns': columns,
        'pk': pk,
        'related_data': nested_related
    })