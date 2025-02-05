from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from controllers import authController

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    return authController.register()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return authController.login()

@auth.route('/logout')
@login_required
def logout():
    return authController.logout()