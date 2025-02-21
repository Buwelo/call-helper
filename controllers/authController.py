from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config.extensions import db, bcrypt
from models import User
import random
import string

def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(first_name=first_name, last_name=last_name, username=username, email=email, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


def login():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').lower()
        last_name = request.form.get('last_name', '').lower()
        email = request.form.get('email', '').lower()
        # password = request.form.get('password', '')

        if not first_name or not last_name or not email:
            flash('First name, last name, and email are required.', 'danger')
            return redirect(url_for('auth.login'))
        remember_me = 'remember' in request.form
        user = User.query.filter_by(email=email).first()

        if user:
            login_user(user=user, remember=remember_me)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            random_digits = ''.join(random.choices(string.digits, k=2))
            username = f"{first_name}_{last_name[:2]}{random_digits}"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')

            user = User(username=username, email=email, password=password_hash,
                first_name=first_name, last_name=last_name)
            print
            db.session.add(user)
            db.session.commit()
            login_user(user=user, remember=remember_me)
            return redirect(url_for('index'))

    return render_template('auth/login.html')


def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))