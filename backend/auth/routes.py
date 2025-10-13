from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user
from auth.models import Admin
import os

auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='templates'  # 👈 This tells Flask to look inside auth/templates
)

login_manager = LoginManager()

# Dummy admin credentials
admin_user = Admin(id=1, username="admin", password="pass123")

@login_manager.user_loader
def load_user(user_id):
    return admin_user if str(admin_user.id) == user_id else None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == admin_user.username and password == admin_user.password:
            login_user(admin_user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')
    