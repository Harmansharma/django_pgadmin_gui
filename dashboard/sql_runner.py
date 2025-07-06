from django.db import connection, DatabaseError
from django.contrib import messages

def run_sql_query(request):
    sql_query = ''
    columns = []
    result = []
    error = None

    if request.method == 'POST':
        if 'clear_query' in request.POST:
            request.session['sql_query'] = ''
            return '', [], [], None

        sql_query = request.POST.get('sql_query', '')
        request.session['sql_query'] = sql_query
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql_query)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchall()
                else:
                    messages.success(request, "✅ Query executed successfully.")
        except DatabaseError as e:
            error = str(e)

    return sql_query, columns, result, error