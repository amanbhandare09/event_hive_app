from flask import Blueprint, render_template, redirect,request,url_for

auth_blueprint = Blueprint('auth',__name__)

@auth_blueprint.route('/signup')
def singup():
    return render_template('signup.html')

@auth_blueprint.route('/signup', methods=['POST'])
def signup_post():
    # Get form data
    email = request.form.get('email')
    name = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone')
    password = request.form.get('password')
    
    # Print to console (for testing)
    print(f"Email: {email}, Name: {name}, Password: {password}, Phone: {phone}, Address: {address}")
    
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
    remember = True if request.form.get('remember') else False
    
    # Print to console (for testing)
    print(f"Email: {email}, Password: {password}, Remember: {remember}")
    
    # Redirect to profile page
    return redirect(url_for('main.profile'))

@auth_blueprint.route("/logout")
def logout():
    return "logout"