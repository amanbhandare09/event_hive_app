from flask import Blueprint, render_template, redirect,request,url_for,flash
from werkzeug.security import generate_password_hash,check_password_hash
from models.model import User
from app import db
from flask_login import login_user, logout_user, login_required, current_user


auth_blueprint = Blueprint('auth',__name__)

@auth_blueprint.route('/signup')
def singup():
    return render_template('signup.html')

@auth_blueprint.route('/signup', methods=['POST'])
def signup_post():
    # Get form data
    email = request.form.get('email')
    username = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()

    if user:
        # User already exists
        print("User already exists!")
        return redirect(url_for('auth.signup'))
    
    # Create new user
    new_user = User(
        email=email,
        username=username,
        password= generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    print(f"New user created: {username}")
    
    # Redirect to login page
    return redirect(url_for('auth.login'))

@auth_blueprint.route("/login")
def login():
    return render_template('login.html')

@auth_blueprint.route('/login', methods=['POST'])
def login_post():
    # Get form data
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Invalid email or password', 'error')
        return redirect(url_for('auth.login'))  # redirect back to login page
    
    login_user(user)
    print(f"Logged in user: {current_user.username}") 

    # Redirect to profile page
    return redirect(url_for('main.profile'))

@auth_blueprint.route("/logout")
@login_required
def logout():
    return "logout"