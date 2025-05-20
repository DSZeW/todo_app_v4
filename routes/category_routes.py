from flask import Blueprint, render_template, request, redirect, session
from db import get_db_connection

category_bp = Blueprint('category', __name__)

@category_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    conn = get_db_connection()
    with conn.cursor() as c:
        c.execute('SELECT id, name FROM categories WHERE user_id = %s', (session['user_id'],))
        categories = c.fetchall()
    conn.close()
    return render_template('categories.html', categories=categories)

@category_bp.route('/categories')
def categories():
    return redirect('/')

@category_bp.route('/add_category', methods=['POST'])
def add_category():
    if 'user_id' not in session:
        return redirect('/login')
    category_name = request.form['category_name']
    conn = get_db_connection()
    with conn.cursor() as c:
        try:
            c.execute('INSERT INTO categories (name, user_id) VALUES (%s, %s)', (category_name, session['user_id']))
            conn.commit()
        except:
            pass
    conn.close()
    return redirect('/')

@category_bp.route('/delete_category', methods=['POST'])
def delete_category():
    if 'user_id' not in session:
        return redirect('/login')
    category_id = request.form['category_to_delete']
    conn = get_db_connection()
    with conn.cursor() as c:
        # 🔐 Vérifie que l’utilisateur peut supprimer uniquement ses propres catégories
        c.execute('DELETE FROM categories WHERE id=%s AND user_id=%s', (category_id, session['user_id']))
        conn.commit()
    conn.close()
    return redirect('/')
