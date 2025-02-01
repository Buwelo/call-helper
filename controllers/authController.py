from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config.extensions import db, bcrypt
from models import User

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
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = 'remember' in request.form
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user=user, remember=remember_me)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('auth/login.html')


def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))