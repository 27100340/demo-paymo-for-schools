from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from pymongo import MongoClient
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import os
import ssl

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Set session lifetime
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.secret_key = 'your-secure-random-secret-key'  # Set a secure, static secret key
app.permanent_session_lifetime = timedelta(days=31)
# MongoDB configuration with error handling
try:
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise ValueError("MongoDB URI not found in environment variables")
    
    # Configure MongoDB client with SSL/TLS settings
    client = MongoClient(
        mongodb_uri,
        tls=True,
        tlsAllowInvalidCertificates=True,
        retryWrites=True,
        w="majority"
    )
    
    app.config["MONGO_URI"] = mongodb_uri
    app.secret_key = os.getenv('FLASK_SECRET_KEY')
    
    # Initialize MongoDB connection
    client.admin.command('ping')
    print("MongoDB connection successful!")
    
    # Test database access
    db = client.paymo_db
    print("Database accessed successfully!")
    
    # Create indexes after confirming connection
    db.students.create_index("username", unique=True)
    db.students.create_index("student_id", unique=True)
    print("Indexes created successfully!")
        
except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    raise

# Make db globally available
mongo = db

# Add this near the top with other configurations
TOPUP_METHODS = ['Credit/Debit Card', 'Bank Transfer']

# Admin credentials (replace with secure storage in production)
ADMIN_CREDENTIALS = {
    'username': os.getenv('ADMIN_USERNAME', 'admin'),
    'password': os.getenv('ADMIN_PASSWORD', 'admin123')
}

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# Split admin login and dashboard into separate routes
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.json
        if (data.get('username') == ADMIN_CREDENTIALS['username'] and 
            data.get('password') == ADMIN_CREDENTIALS['password']):
            session['admin_logged_in'] = True
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    return render_template('admin_login.html')

@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    # Fetch all students from MongoDB
    students = list(mongo.students.find())
    # Convert ObjectId to string for rendering
    for student in students:
        student['_id'] = str(student['_id'])
    return render_template('admin_users.html', users=students)

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)  # Only remove admin session key
    return redirect(url_for('admin_login'))

@app.route('/students')
def student_table():
    # Fetch all students from MongoDB
    students = list(mongo.students.find())
    
    table_rows = ""
    for student in students:
        table_rows += f"""
        <tr>
            <td>{student['student_id']}</td>
            <td>{student['name']}</td>
            <td>{student['school']}</td>
            <td>{student['balance']}</td>
        </tr>
        """

    html = f"""
    <html>
        <head>
            <title>Students Table</title>
            <style>
                table {{ border-collapse: collapse; width: 60%; margin: auto; }}
                th, td {{ border: 1px solid #aaa; padding: 8px; text-align: center; }}
                th {{ background-color: #f2f2f2; }}
                h2 {{ text-align: center; }}
            </style>
        </head>
        <body>
            <h2>Student Records</h2>
            <table>
                <tr>
                    <th>Student ID</th>
                    <th>Name</th>
                    <th>School</th>
                    <th>Balance</th>
                </tr>
                {table_rows}
            </table>
        </body>
    </html>
    """
    return html

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        student_id = data.get('student_id')
        
        # Check if username or student_id already exists
        if mongo.students.find_one({"username": username}):
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
            
        if mongo.students.find_one({"student_id": student_id}):
            return jsonify({'status': 'error', 'message': 'Student ID already registered'}), 400
            
        new_student = {
            'username': username,
            'password': data.get('password'),  # In production, hash this password
            'name': data.get('name'),
            'school': data.get('school'),
            'student_id': student_id,
            'balance': 0,
            'transactions': [],
            'created_at': datetime.utcnow()
        }
        
        mongo.students.insert_one(new_student)
        return jsonify({'status': 'success'})
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        student = mongo.students.find_one({
            "username": data.get('username'),
            "password": data.get('password')  # In production, verify hashed password
        })
        print(student)
        if student:
            # Make session permanent and set user data
            session.permanent = True
            session['username'] = student['username']
            session['student_id'] = student['student_id']
            session['school'] = student['school']
            session['name'] = student['name']  # Add name to session
            
            # Convert ObjectId to string for JSON serialization
            student['_id'] = str(student['_id'])
            
            return jsonify({
                'status': 'success',
                'name': student['name'],
                'balance': student['balance'],
                'transactions': student['transactions']
            })
        return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401
    return render_template('login.html')

# Add this new route for topup page
@app.route('/topup-page')
def topup_page():
    return render_template('topup.html', methods=TOPUP_METHODS)

# Modify the existing topup route
@app.route('/topup', methods=['POST'])
def topup():
    data = request.json
    username = session.get('username')
    amount = float(data.get('amount', 0))
    method = data.get('method')
    
    if not username:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        
    timestamp = datetime.utcnow()
    
    result = mongo.students.update_one(
        {"username": username},
        {
            "$inc": {"balance": amount},
            "$push": {
                "transactions": {
                    "type": "topup",
                    "amount": amount,
                    "timestamp": timestamp,
                    "method": method
                }
            }
        }
    )
    
    if result.modified_count:
        student = mongo.students.find_one({"username": username})
        return jsonify({
            'status': 'success',
            'new_balance': student['balance'],
            'transactions': student['transactions']
        })
    return jsonify({'status': 'error', 'message': 'Update failed'}), 500

@app.route('/send', methods=['POST'])
def send_money():
    data = request.json
    sender_username = session.get('username')
    recipient_id = data.get('recipient_id')
    recipient_school = data.get('recipient_school')
    amount = float(data.get('amount', 0))

    sender = mongo.students.find_one({"username": sender_username})
    recipient = mongo.students.find_one({
        "student_id": recipient_id,
        "school": recipient_school
    })

    if not sender:
        return jsonify({'status': 'error', 'message': 'Sender not found'}), 404
    if not recipient:
        return jsonify({'status': 'error', 'message': 'Recipient not found'}), 404
    if sender['balance'] < amount:
        return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

    timestamp = datetime.utcnow()

    # Update sender
    mongo.students.update_one(
        {"username": sender_username},
        {
            "$inc": {"balance": -amount},
            "$push": {
                "transactions": {
                    "type": "sent",
                    "amount": amount,
                    "timestamp": timestamp,
                    "with": recipient['name'],
                    "school": recipient['school']
                }
            }
        }
    )

    # Update recipient
    mongo.students.update_one(
        {"student_id": recipient_id},
        {
            "$inc": {"balance": amount},
            "$push": {
                "transactions": {
                    "type": "received",
                    "amount": amount,
                    "timestamp": timestamp,
                    "with": sender['name'],
                    "school": sender['school']
                }
            }
        }
    )

    updated_sender = mongo.students.find_one({"username": sender_username})
    return jsonify({
        'status': 'success',
        'sender_balance': updated_sender['balance'],
        'transactions': updated_sender['transactions']
    })

@app.route('/admin/users')
@admin_required
def admin_users():
    # Fetch all students from MongoDB
    students = list(mongo.students.find())
    # Convert ObjectId to string for rendering
    for student in students:
        student['_id'] = str(student['_id'])
    return render_template('admin_users.html', users=students)

@app.route('/admin/update-user', methods=['POST'])
@admin_required
def admin_update_user():
    if not session.get('admin_logged_in'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401

    data = request.json
    username = data.get('username')
    action = data.get('action')

    if not username or not action:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    if action == 'delete':
        result = mongo.students.delete_one({"username": username})
        if result.deleted_count:
            return jsonify({'status': 'success', 'message': 'User deleted successfully'})
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    elif action == 'update':
        if mongo.students.find_one({"username": username}):
            if 'password' in data and data['password']:
                mongo.students.update_one(
                    {"username": username},
                    {"$set": {"password": data['password']}}
                )
            return jsonify({'status': 'success', 'message': 'User updated successfully'})
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    return jsonify({'status': 'error', 'message': 'Invalid action'}), 400

@app.route('/logout')
def logout():
    # Only remove student-related session keys
    session.pop('username', None)
    session.pop('student_id', None)
    session.pop('school', None)
    session.pop('name', None)

    session.clear()
    return redirect(url_for('login'))

@app.route('/get-user-data', methods=['GET'])  # Use GET since no data is being modified
def get_user_data():
    if 'username' not in session:
        print("username not found")
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    
    student = mongo.students.find_one({"username": session['username']})
    if student:
        student['_id'] = str(student['_id'])
        return jsonify({
            'status': 'success',
            'name': student['name'],
            'balance': student['balance'],
            'transactions': student['transactions']
        })
    return jsonify({'status': 'error', 'message': 'User not found'}), 404
# Add a route to check session status
@app.route('/check-session')
def check_session():
    if 'username' in session:
        student = mongo.students.find_one({"username": session['username']})
        if student:
            # Convert ObjectId to string for JSON serialization
            student['_id'] = str(student['_id'])
            return jsonify({
                'status': 'success',
                'logged_in': True,
                'username': student['username'],  # Ensure correct username is returned
                'name': student['name'],
                'balance': student['balance'],
                'transactions': student['transactions']
            })
        else:
            # If the student is not found, clear the session to prevent stale data
            session.pop('username', None)
            session.pop('student_id', None)
            session.pop('school', None)
            session.pop('name', None)
            return jsonify({
                'status': 'error',
                'logged_in': False,
                'message': 'User not found in database'
            }), 404
    return jsonify({
        'status': 'error',
        'logged_in': False,
        'message': 'Not logged in'
    }), 401

@app.before_request
def check_db_connection():
    try:
        # Ping the database
        client.admin.command('ping')
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        # Reconnect if needed
        if 'username' in session or 'admin_logged_in' in session:
            session.clear()
        return jsonify({'status': 'error', 'message': 'Database connection error'}), 500

if __name__ == '__main__':
    app.run(debug=True)