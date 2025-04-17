from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key in production

# Admin credentials (in production, use proper password hashing and store in database)
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

# Add this near the top with other configurations
TOPUP_METHODS = ['Credit/Debit Card', 'Bank Transfer']

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Simulated in-memory student database
students = {
    'user123': {
        'username': 'user123',
        'password': 'pass123',  # In production, use proper password hashing
        'name': 'Talah Ahmed',
        'school': 'LGS',
        'student_id': '12345',
        'balance': 1000,
        'transactions': []
    },
    'user456': {
        'username': 'user456',
        'password': 'pass456',
        'name': 'Tahir',
        'school': 'LGS',
        'student_id': '67890',
        'balance': 500,
        'transactions': []
    }
}

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
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
    return render_template('admin_users.html', users=students)

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/students')
def student_table():
    table_rows = ""
    for username, info in students.items():
        table_rows += f"""
        <tr>
            <td>{info['student_id']}</td>
            <td>{info['name']}</td>
            <td>{info['school']}</td>
            <td>{info['balance']}</td>
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
        for existing_user in students.values():
            if existing_user.get('student_id') == student_id:
                return jsonify({'status': 'error', 'message': 'Student ID already registered'}), 400
                
        if username in students:
            return jsonify({'status': 'error', 'message': 'Username already exists'}), 400
            
        students[username] = {
            'password': data.get('password'),
            'name': data.get('name'),
            'school': data.get('school'),
            'student_id': student_id,
            'balance': 0,
            'transactions': []
        }
        return jsonify({'status': 'success'})
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if username in students and students[username]['password'] == password:
            session['username'] = username
            session['student_id'] = students[username]['student_id']
            session['school'] = students[username]['school']
            return jsonify({
                'status': 'success',
                'name': students[username]['name'],
                'balance': students[username]['balance'],
                'transactions': students[username]['transactions']
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
    username = session.get('username')  # Get username from session instead of request
    amount = float(data.get('amount', 0))
    method = data.get('method')
    
    if username and username in students:
        students[username]['balance'] += amount
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Record the topup transaction
        students[username]['transactions'].append({
            'type': 'topup',
            'amount': amount,
            'timestamp': timestamp,
            'method': method
        })
        
        return jsonify({
            'status': 'success', 
            'new_balance': students[username]['balance'],
            'transactions': students[username]['transactions']
        })
    return jsonify({'status': 'error', 'message': 'Student not found'}), 404

@app.route('/send', methods=['POST'])
def send_money():
    data = request.json
    sender_username = session.get('username')  # Get sender from session
    recipient_id = data.get('recipient_id')
    recipient_school = data.get('recipient_school')
    amount = float(data.get('amount', 0))

    # Find recipient by student ID and school
    recipient_username = None
    for username, user in students.items():
        if user['student_id'] == recipient_id and user['school'] == recipient_school:
            recipient_username = username
            break

    if not sender_username or sender_username not in students:
        return jsonify({'status': 'error', 'message': 'Sender not found'}), 404
    if not recipient_username:
        return jsonify({'status': 'error', 'message': 'Recipient not found'}), 404

    if students[sender_username]['balance'] < amount:
        return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Record transaction for sender
    students[sender_username]['balance'] -= amount
    students[sender_username]['transactions'].append({
        'type': 'sent',
        'amount': amount,
        'timestamp': timestamp,
        'with': students[recipient_username]['name'],
        'school': students[recipient_username]['school']
    })

    # Record transaction for recipient
    students[recipient_username]['balance'] += amount
    students[recipient_username]['transactions'].append({
        'type': 'received',
        'amount': amount,
        'timestamp': timestamp,
        'with': students[sender_username]['name'],
        'school': students[sender_username]['school']
    })

    return jsonify({
        'status': 'success',
        'sender_balance': students[sender_username]['balance'],
        'transactions': students[sender_username]['transactions']
    })

@app.route('/admin/users')
@admin_required
def admin_users():
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
        if username in students:
            del students[username]
            return jsonify({'status': 'success', 'message': 'User deleted successfully'})
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    elif action == 'update':
        if username in students:
            if 'password' in data and data['password']:
                students[username]['password'] = data['password']
            return jsonify({'status': 'success', 'message': 'User updated successfully'})
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    return jsonify({'status': 'error', 'message': 'Invalid action'}), 400

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('student_id', None)
    session.pop('school', None)
    return redirect(url_for('login'))

@app.route('/get-user-data', methods=['POST'])
def get_user_data():
    data = request.json
    username = data.get('username')
    
    if username and username in students:
        return jsonify({
            'status': 'success',
            'name': students[username]['name'],
            'balance': students[username]['balance'],
            'transactions': students[username]['transactions']
        })
    return jsonify({'status': 'error', 'message': 'User not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
