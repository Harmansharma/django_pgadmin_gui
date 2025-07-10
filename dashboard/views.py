import re
from django.shortcuts import render, redirect
from django.apps import apps
from django.forms import modelform_factory
from django.db import connection, DatabaseError
from django.http import Http404
from django.contrib import messages
from .utils import get_all_tables 
from .sql_runner import run_sql_query
from .utils import get_all_tables_with_columns
from django.views.decorators.csrf import csrf_exempt


RESERVED_WORDS = {
    'select', 'from', 'where', 'table', 'insert', 'update', 'delete',
    'join', 'order', 'group', 'by', 'limit', 'primary', 'key', 'foreign'
}


@csrf_exempt




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
                    cursor.execute("SET TIME ZONE 'Asia/Kolkata';")
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
                cursor.execute("SET TIME ZONE 'Asia/Kolkata';")
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
                print(f" Default timestamp set for {column} in table {table_name}")
            else:
                print(f" Column {column} already has a default or does not exist.")

    except DatabaseError as e:
        print(f" Failed to set default on {table_name}.{column}: {str(e)}")


def is_valid_identifier(name):
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name)) and name.lower() not in RESERVED_KEYWORDS



def create_table_view(request):
    error = None
    generated_sql = None
    table_name = ''
    columns = []
    data_types = []
    primary_keys = []
    not_nulls = []
    uniques = []
    default_values = []
    foreign_keys = []
    reference_tables = []
    add_index = []
    include_created = True
    include_updated = True  

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT kcu.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
        """)
        fk_candidates = cursor.fetchall()  # [('users', 'id'), ('products', 'product_id')]

    if request.method == 'POST':
        table_name = request.POST.get('table_name', '').strip()
        columns = request.POST.getlist('column_name[]')
        data_types = request.POST.getlist('data_type[]')
        primary_keys = request.POST.getlist('primary_key[]')
        not_nulls = request.POST.getlist('not_null[]')
        uniques = request.POST.getlist('unique[]')
        default_values = request.POST.getlist('default_value[]')
        foreign_keys = request.POST.getlist('foreign_key[]')
        reference_tables = request.POST.getlist('reference_table[]')
        add_index = request.POST.getlist('add_index[]')
        include_created = request.POST.get('include_created')
        include_updated = request.POST.get('include_updated')

        if not table_name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            error = " Invalid table name."
        elif any(col.strip().lower() in RESERVED_WORDS for col in columns):
            error = " One or more column names are reserved words."
        elif len(set(columns)) != len(columns):
            error = " Duplicate column names are not allowed."
        elif not all(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col.strip()) for col in columns):
            error = "Invalid column names. Use only letters, numbers, and underscores."

        if not error:
            col_defs = []
            fk_constraints = []
            index_statements = []

            for i in range(len(columns)):
                col = columns[i].strip()
                dtype = data_types[i].strip().upper()

                if col in primary_keys and dtype == "INTEGER":
                    dtype = "SERIAL"

                definition = f"{col} {dtype}"

                if col in not_nulls:
                    definition += " NOT NULL"
                if col in uniques:
                    definition += " UNIQUE"
                if default_values[i].strip():
                    default = default_values[i].strip()
                    if not default.isdigit() and default.upper() not in ('TRUE', 'FALSE', 'CURRENT_TIMESTAMP', 'NOW()'):
                        default = f"'{default}'"
                    definition += f" DEFAULT {default}"

                col_defs.append(definition)

                if i < len(foreign_keys) and foreign_keys[i] == "on":
                    if i < len(reference_tables):
                        fk_ref = reference_tables[i].strip()
                        if fk_ref:
                            try:
                                ref_table, ref_column = fk_ref.rstrip(')').split('(')
                                fk_constraints.append(f'FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_column})')
                            except ValueError:
                                error = f"❌ Invalid foreign key format for: {fk_ref}"
                                break

                # Index
                if i < len(add_index) and add_index[i] == "on":
                    index_statements.append(f'CREATE INDEX idx_{table_name}_{col} ON {table_name} ({col});')

            if not error:
                pk_cleaned = [pk for pk in primary_keys if pk.strip()]
                if pk_cleaned:
                    col_defs.append(f"PRIMARY KEY ({', '.join(pk_cleaned)})")

                col_defs.extend(fk_constraints)

                # Audit columns
                if include_created:
                    col_defs.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                if include_updated:
                    col_defs.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

                generated_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(col_defs) + "\n);"

                # Only preview
                if 'preview_sql' in request.POST:
                    return render(request, 'dashboard/create_table.html', {
                        'generated_sql': generated_sql,
                        'error': error,
                        'table_name': table_name,
                        'columns_data': zip(columns, data_types, default_values, not_nulls, uniques, primary_keys, foreign_keys, reference_tables, add_index),
                        'include_created': include_created,
                        'include_updated': include_updated,
                        'fk_candidates': fk_candidates
                    })

                # Execute SQL
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(generated_sql)
                        for index_sql in index_statements:
                            cursor.execute(index_sql)

                    messages.success(request, f" Table '{table_name}' created successfully!")
                    return redirect('dashboard_home')

                except DatabaseError as e:
                    error = f" Database Error: {str(e)}"

    return render(request, 'dashboard/create_table.html', {
        'generated_sql': generated_sql,
        'error': error,
        'table_name': table_name,
        'columns_data': zip(columns, data_types, default_values, not_nulls, uniques, primary_keys, foreign_keys, reference_tables, add_index),
        'include_created': include_created,
        'include_updated': include_updated,
        'fk_candidates': fk_candidates
    })

def edit_table_view(request, table_name):
    if request.method == 'POST':
        try:
            old_names = request.POST.getlist('old_column_name[]')
            new_names = request.POST.getlist('new_column_name[]')
            data_types = request.POST.getlist('data_type[]')
            nullable = request.POST.getlist('nullable[]')
            drop_columns = request.POST.getlist('drop_column[]')
            index_fields = request.POST.getlist('add_index[]')

            new_col_names = request.POST.getlist('new_column_name_only[]')
            new_col_types = request.POST.getlist('new_column_type[]')
            new_col_nullable = request.POST.getlist('new_column_nullable[]')
            new_col_fks = request.POST.getlist('new_column_fk[]')

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = %s AND table_schema = 'public'
                """, [table_name])
                existing_columns = [row[0] for row in cursor.fetchall()]

            alter_statements = []
            index_statements = []  #  Indexes will be handled separately

            for i in range(len(old_names)):
                old = old_names[i].strip()
                new = new_names[i].strip()
                dtype = data_types[i].strip()
                is_nullable = old in nullable
                is_drop = old in drop_columns

                if is_drop:
                    alter_statements.append(f'DROP COLUMN "{old}"')
                    continue

                if old != new:
                    alter_statements.append(f'RENAME COLUMN "{old}" TO "{new}"')

                alter_statements.append(f'ALTER COLUMN "{new}" TYPE {dtype}')
                alter_statements.append(f'ALTER COLUMN "{new}" {"DROP" if is_nullable else "SET"} NOT NULL')

                if new in index_fields:
                    index_statements.append(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_{new} ON "{table_name}"("{new}")')

            adding_new_columns = any(name.strip() for name in new_col_names)
            if adding_new_columns:
                if 'created_at' not in existing_columns:
                    alter_statements.append('ADD COLUMN "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL')
                if 'updated_at' not in existing_columns:
                    alter_statements.append('ADD COLUMN "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL')

            for i in range(len(new_col_names)):
                name = new_col_names[i].strip()
                if not name:
                    continue

                dtype = new_col_types[i].strip() or 'TEXT'
                is_nullable = str(i) in new_col_nullable
                fk = new_col_fks[i].strip()

                col_def = f'"{name}" {dtype}'

                if not is_nullable:
                    col_def += ' NOT NULL'

                alter_statements.append(f'ADD COLUMN {col_def}')

                if fk and '.' in fk:
                    ref_table, ref_column = fk.split('.')
                    constraint_name = f'fk_{table_name}_{name}'
                    alter_statements.append(
                        f'ADD CONSTRAINT {constraint_name} FOREIGN KEY ("{name}") REFERENCES "{ref_table}"("{ref_column}")'
                    )

                if f'new_{i}' in index_fields:
                    index_statements.append(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_{name} ON "{table_name}"("{name}")')

            if alter_statements:
                full_sql = f'ALTER TABLE "{table_name}"\n  ' + ',\n  '.join(alter_statements) + ';'
                with connection.cursor() as cursor:
                    cursor.execute(full_sql)

            #  Now execute CREATE INDEX separately
            for stmt in index_statements:
                with connection.cursor() as cursor:
                    cursor.execute(stmt)

            if alter_statements or index_statements:
                messages.success(request, f" Changes applied to table '{table_name}' successfully!")
            else:
                messages.info(request, "No changes were submitted.")

            return redirect('edit_table_view', table_name=table_name)

        except DatabaseError as e:
            messages.error(request, f" Error: {str(e)}")
            return redirect('edit_table_view', table_name=table_name)

    # GET request: Load existing column metadata
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
        """, [table_name])
        columns = cursor.fetchall()

    formatted_columns = []
    for col in columns:
        formatted_columns.append({
            'name': col[0],
            'data_type': col[1],
            'nullable': col[2] == 'YES',
        })

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT table_name, column_name FROM information_schema.columns
            WHERE table_schema = 'public'
        """)
        fk_candidates = cursor.fetchall()

    return render(request, 'dashboard/edit_table.html', {
        'table_name': table_name,
        'columns': formatted_columns,
        'fk_candidates': fk_candidates
    })

def drop_table_view(request, table_name):
    if request.method == 'POST':
        try:
            with connection.cursor() as cursor:
                #  Correct FK dependency check
                cursor.execute("""
                    SELECT tc.table_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.constraint_schema = kcu.constraint_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.constraint_schema = tc.constraint_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND ccu.table_name = %s;
                """, [table_name])
                
                references = cursor.fetchall()

                if references:
                    dependent_tables = ", ".join(set(r[0] for r in references))
                    messages.error(
                        request,
                        f" Cannot drop table '{table_name}' because it is referenced by: {dependent_tables}"
                    )
                    return redirect('dashboard_home')

                # Safe to drop
                cursor.execute(f'DROP TABLE "{table_name}" CASCADE')  # optional: CASCADE
                messages.success(request, f"Table '{table_name}' dropped successfully!")
                return redirect('dashboard_home')

        except DatabaseError as e:
            messages.error(request, f" Database error: {str(e)}")
            return redirect('dashboard_home')

    messages.warning(request, " Invalid request method.")
    return redirect('dashboard_home')

     
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