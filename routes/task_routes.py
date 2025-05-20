from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime
from db import get_db_connection
from google_calendar import add_event_to_google_calendar

# Blueprint dédié aux tâches
task_bp = Blueprint('task_bp', __name__)

@task_bp.app_template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y à %H:%M'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

@task_bp.route('/delete/<int:id>')
def delete_task(id):
    next_page = request.args.get('next', '/')
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute('DELETE FROM tasks WHERE id=%s AND user_id=%s', (id, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(next_page)

@task_bp.route('/complete/<int:id>')
def complete_task(id):
    next_page = request.args.get('next', '/')
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute('UPDATE tasks SET completed=1, status_id=3 WHERE id=%s AND user_id=%s', (id, session['user_id']))
        conn.commit()
    conn.close()
    return redirect(next_page)

@task_bp.route('/comment/<int:task_id>', methods=['POST'])
def add_comment(task_id):
    if 'user_id' not in session:
        return redirect('/login')

    next_page = request.args.get('next', '/')
    comment_text = request.form['comment']
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute('INSERT INTO comments (task_id, comment) VALUES (%s, %s)', (task_id, comment_text))
        conn.commit()
    conn.close()
    return redirect(next_page)

@task_bp.route('/category/<int:category_id>')
def tasks_by_category(category_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    with conn.cursor() as c:
        # Vérifie que la catégorie appartient bien à l'utilisateur
        c.execute('SELECT name FROM categories WHERE id=%s AND user_id=%s', (category_id, session['user_id']))
        result = c.fetchone()
        if not result:
            conn.close()
            return redirect('/all_tasks')  # Redirection si catégorie inexistante ou interdite
        category_name = result[0]

        c.execute('''
            SELECT tasks.id, tasks.title, tasks.completed, categories.name, priorities.level, statuses.name, tasks.created_at, assigned_persons.name
            FROM tasks
            JOIN categories ON tasks.category_id = categories.id
            JOIN priorities ON tasks.priority_id = priorities.id
            JOIN statuses ON tasks.status_id = statuses.id
            LEFT JOIN assigned_persons ON tasks.assigned_person_id = assigned_persons.id
            WHERE tasks.user_id=%s AND tasks.category_id=%s
            ''', (session['user_id'], category_id))

        tasks_data = c.fetchall()

        # Récupère tous les commentaires liés à ces tâches
        c.execute('SELECT task_id, comment FROM comments')
        comments_data = c.fetchall()

    comments = {}
    for task_id, comment in comments_data:
        comments.setdefault(task_id, []).append(comment)

    tasks_by_status = {'Non commencée': [], 'En cours': [], 'Terminée': []}
    for task in tasks_data:
        tasks_by_status[task[5]].append(task)

    conn.close()
    return render_template('tasks.html', tasks_by_status=tasks_by_status, comments=comments,
                           category_name=category_name, current_category_id=category_id)

@task_bp.route('/start/<int:id>')
def start_task(id):
    next_page = request.args.get('next', '/')
    conn = get_db_connection()
    with conn.cursor() as c:
        # Récupère les infos utiles de la tâche
        c.execute('''
            SELECT tasks.title, tasks.start_datetime, categories.name 
            FROM tasks 
            JOIN categories ON tasks.category_id = categories.id
            WHERE tasks.id=%s AND tasks.user_id=%s
        ''', (id, session['user_id']))
        task_data = c.fetchone()

        # Met à jour le statut de la tâche
        c.execute('UPDATE tasks SET status_id=2 WHERE id=%s AND user_id=%s', (id, session['user_id']))
        conn.commit()

    conn.close()

    # Si une date de début est renseignée, ajoute dans l'agenda Google
    if task_data and task_data[1]:
        title = f"{task_data[0]} ({task_data[2]})"
        start_datetime = task_data[1].strftime('%Y-%m-%dT%H:%M:%S')
        try:
            add_event_to_google_calendar(title, start_datetime)
        except Exception as e:
            print(f"[⚠️] Erreur lors de l’ajout à Google Calendar : {e}")

    return redirect(next_page)

@task_bp.app_template_filter('datetimeformat')
def datetimeformat(value, format='%d/%m/%Y à %H:%M'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

@task_bp.route('/all_tasks')
def all_tasks():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute('''
            SELECT tasks.id, tasks.title, tasks.completed, categories.name, priorities.level, statuses.name,
                   tasks.created_at, assigned_persons.name, tasks.start_datetime
            FROM tasks
            JOIN categories ON tasks.category_id = categories.id
            JOIN priorities ON tasks.priority_id = priorities.id
            JOIN statuses ON tasks.status_id = statuses.id
            LEFT JOIN assigned_persons ON tasks.assigned_person_id = assigned_persons.id
            WHERE tasks.user_id=%s
        ''', (session['user_id'],))
        tasks_data = c.fetchall()

        c.execute('SELECT task_id, comment FROM comments')
        comments_data = c.fetchall()

    comments = {}
    for task_id, comment in comments_data:
        comments.setdefault(task_id, []).append(comment)

    tasks_by_status = {'Non commencée': [], 'En cours': [], 'Terminée': []}
    for task in tasks_data:
        tasks_by_status[task[5]].append(task)

    conn.close()
    return render_template('tasks.html', tasks_by_status=tasks_by_status, comments=comments,
                           category_name=None, current_category_id=None)

@task_bp.route('/add', methods=['GET', 'POST'])
def add_task():
    category_id_param = request.args.get('category_id')
    next_page = request.args.get('next', '/')

    conn = get_db_connection()
    with conn.cursor() as c:
        if request.method == 'POST':
            title = request.form['title']
            category_id = request.form['category']
            priority_id = request.form['priority']
            comment = request.form.get('comment', '')
            start_datetime_str = request.form.get('start_datetime', '')
            assigned_person_name = request.form.get('assigned_person_name', '').strip()
            next_redirect = request.form.get('next', '/')

            # Convertir la date pour MySQL
            start_datetime = None
            if start_datetime_str:
                start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')

            assigned_person_id = None
            if assigned_person_name:
                c.execute('SELECT id FROM assigned_persons WHERE name=%s AND user_id=%s',
                          (assigned_person_name, session['user_id']))
                existing = c.fetchone()
                if existing:
                    assigned_person_id = existing[0]
                else:
                    c.execute('INSERT INTO assigned_persons (name, user_id) VALUES (%s, %s)',
                              (assigned_person_name, session['user_id']))
                    assigned_person_id = c.lastrowid

            c.execute('''
                INSERT INTO tasks (user_id, title, category_id, priority_id, status_id, assigned_person_id, start_datetime)
                VALUES (%s, %s, %s, %s, 1, %s, %s)
            ''', (session['user_id'], title, category_id, priority_id, assigned_person_id, start_datetime))
            task_id = c.lastrowid

            if comment.strip():
                c.execute('INSERT INTO comments (task_id, comment) VALUES (%s, %s)', (task_id, comment))

            conn.commit()
            conn.close()
            return redirect(next_redirect)

        c.execute('SELECT id, name FROM categories')
        categories = c.fetchall()
        c.execute('SELECT id, level FROM priorities')
        priorities = c.fetchall()

    conn.close()
    return render_template('add_task.html', categories=categories, priorities=priorities,
                           selected_category_id=category_id_param, next_page=next_page)

@task_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    next_page = request.args.get('next', '/')
    conn = get_db_connection()
    with conn.cursor() as c:
        if request.method == 'POST':
            title = request.form['title']
            category_id = request.form['category']
            priority_id = request.form['priority']
            status_id = request.form['status']
            assigned_person_name = request.form.get('assigned_person_name', '').strip()
            start_datetime_str = request.form.get('start_datetime', '')
            start_datetime = None
            if start_datetime_str:
                start_datetime = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')

            assigned_person_id = None
            if assigned_person_name:
                c.execute('SELECT id FROM assigned_persons WHERE name=%s AND user_id=%s',
                          (assigned_person_name, session['user_id']))
                existing = c.fetchone()
                if existing:
                    assigned_person_id = existing[0]
                else:
                    c.execute('INSERT INTO assigned_persons (name, user_id) VALUES (%s, %s)',
                              (assigned_person_name, session['user_id']))
                    assigned_person_id = c.lastrowid

            c.execute('''
                UPDATE tasks
                SET title=%s, category_id=%s, priority_id=%s, status_id=%s, assigned_person_id=%s, start_datetime=%s
                WHERE id=%s AND user_id=%s
            ''', (title, category_id, priority_id, status_id, assigned_person_id, start_datetime, id, session['user_id']))

            conn.commit()
            conn.close()
            return redirect(next_page)

        c.execute('''
            SELECT title, category_id, priority_id, status_id, assigned_person_id, start_datetime
            FROM tasks WHERE id=%s AND user_id=%s
        ''', (id, session['user_id']))
        task = c.fetchone()

        assigned_person_name = ''
        if task[4]:
            c.execute('SELECT name FROM assigned_persons WHERE id=%s', (task[4],))
            result = c.fetchone()
            if result:
                assigned_person_name = result[0]

        start_datetime_value = ''
        if task[5]:
            start_datetime_value = task[5].strftime('%Y-%m-%dT%H:%M')

        c.execute('SELECT id, name FROM categories')
        categories = c.fetchall()
        c.execute('SELECT id, level FROM priorities')
        priorities = c.fetchall()
        c.execute('SELECT id, name FROM statuses')
        statuses = c.fetchall()

    conn.close()
    return render_template('edit_task.html',
                           task=task,
                           categories=categories,
                           priorities=priorities,
                           statuses=statuses,
                           task_id=id,
                           next_page=next_page,
                           assigned_person_name=assigned_person_name,
                           start_datetime_value=start_datetime_value)

