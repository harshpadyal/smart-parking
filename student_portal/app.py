from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from models.db_config import students_collection
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from datetime import timedelta
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=7)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        vesit_id = request.form['vesit_id']
        
        # Check if user exists
        existing_user = students_collection.find_one({"$or": [{"email": email}, {"vesit_id": vesit_id}]})
        if existing_user:
            flash("User with same email or VESIT ID already exists.", "error")
            return redirect(url_for('register'))

        # Create new user
        hashed_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        student = {
            "name": request.form['name'],
            "email": email,
            "batch": request.form['batch'],
            "branch": request.form['branch'],
            "division": request.form['division'],
            "vesit_id": vesit_id,
            "license_plate": request.form['license_plate'],
            "password": hashed_password
        }
        students_collection.insert_one(student)
        flash("Registration successful. Please login.")
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    user = students_collection.find_one({'email': email})

    if user and check_password_hash(user['password'], password):
        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['name'] = user['name']
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid email or password", "danger")
        return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return send_from_directory(app.static_folder, 'available.html')
    else:
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)