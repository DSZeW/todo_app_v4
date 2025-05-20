from flask import Blueprint, render_template, request, redirect, session
import bcrypt
from db import get_db_connection
import re
import pymysql

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        conn = get_db_connection()
        with conn.cursor() as c:
            c.execute('SELECT id, password FROM users WHERE username=%s', (username,))
            user = c.fetchone()
            if user and bcrypt.checkpw(password, user[1].encode('utf-8')):
                session['user_id'] = user[0]
                c.execute('INSERT INTO connections_log (user_id) VALUES (%s)', (user[0],))
                conn.commit()
                return redirect('/')
        conn.close()
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    error = None  # Prépare la variable d’erreur
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password_raw = request.form['password']

        # Vérifie l'email
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            error = "Adresse email invalide."
        else:
            # Vérifie le mot de passe
            password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
            if not re.match(password_regex, password_raw):
                error = "Mot de passe trop faible : 8 caractères, 1 majuscule, 1 chiffre, 1 spécial."

        if not error:
            # Si tout est OK, enregistre
            password = bcrypt.hashpw(password_raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = get_db_connection()
            with conn.cursor() as c:
                try:
                    c.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, password))
                    conn.commit()
                    conn.close()
                    return redirect('/login')
                except pymysql.IntegrityError:
                    error = "Nom d'utilisateur ou e-mail déjà utilisé."
                    conn.close()

    # Affiche la page avec le message d'erreur s’il existe
    return render_template('register.html', error=error)


@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')
