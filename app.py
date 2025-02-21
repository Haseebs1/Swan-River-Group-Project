from flask import Flask, redirect, url_for, session, request, render_template, jsonify
import msal
import requests
import os
import pyodbc
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='docs', static_folder='docs')
app.secret_key = os.getenv('SECRET_KEY')  # Required for session management

# Azure AD configuration
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
TENANT_ID = os.getenv('TENANT_ID')
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = ['User.Read']

# Your database connection string
conn_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:swan-river123.database.windows.net,1433;Database=Swan-River;Uid=swanriver;Pwd=Admin123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={conn_string}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    __tablename__ = 'User' # Explicitly sets table name to match table in Azure database
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), default="basicuser")
    status = db.Column(db.String(20), default="active")

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Login page
@app.route('/login')
def login():
    return render_template('login.html')

# Initiate Microsoft 365 login
@app.route('/azure_login')
def azure_login():
    session['state'] = os.urandom(16).hex()  # Generate a random state for security
    auth_url = _build_auth_url(scopes=SCOPE, state=session['state'])
    return redirect(auth_url)

# Callback route after Microsoft 365 login
@app.route('/auth/callback')
def authorized():
    if request.args.get('state') != session.get('state'):
        return redirect(url_for('index'))  # Prevent CSRF attacks

    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))

    token = _get_token_from_code(code)
    if not token:
        return redirect(url_for('index'))

    user_info = _get_user_info(token)
    if not user_info:
        return redirect(url_for('index'))

    session['user'] = user_info
    return redirect(url_for('success'))

# Success page after login
@app.route('/success')
def success():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin.html', user_name=user_name)

# CRUD routes for User model

# Create User
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    new_user = User(name=data['name'], email=data['email'], role=data.get('role', 'basicuser'), status=data.get('status', 'active'))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

# Read Users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_list = [{'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role, 'status': user.status} for user in users]
    return jsonify(user_list)

# Update User
@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    user.name = data['name']
    user.email = data['email']
    user.role = data.get('role', user.role)
    user.status = data.get('status', user.status)
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

# Delete User
@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

# Route to test database connection
@app.route('/test-db-connection')
def test_db_connection():
    try:
        with pyodbc.connect(conn_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                return jsonify({'message': 'Database connection successful', 'result': result[0]})
    except Exception as e:
        return jsonify({'error': str(e), 'connection_string': conn_string})

# Helper function to build the authorization URL
def _build_auth_url(scopes=None, state=None):
    return msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY).get_authorization_request_url(
        scopes, state=state, redirect_uri=REDIRECT_URI)

# Helper function to get the access token
def _get_token_from_code(code):
    try:
        client = msal.ConfidentialClientApplication(
            CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
        result = client.acquire_token_by_authorization_code(
            code, scopes=SCOPE, redirect_uri=REDIRECT_URI)
        return result.get('access_token')
    except Exception as e:
        print(f"Error acquiring token: {e}")
        return None

# Helper function to get user info from Microsoft Graph
def _get_user_info(token):
    try:
        graph_data = requests.get(
            'https://graph.microsoft.com/v1.0/me',
            headers={'Authorization': 'Bearer ' + token}).json()
        return graph_data
    except Exception as e:
        print(f"Error fetching user info: {e}")
        return None

if __name__ == '__main__':
    # Create database tables (if they don't exist)
    with app.app_context():
        db.create_all()
    app.run()


'''from flask import Flask, jsonify
import pyodbc

app = Flask(__name__)

# Your database connection string
conn_string = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:swan-river123.database.windows.net,1433;Database=Swan-River;Uid=swanriver;Pwd=Admin123;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

@app.route('/')
def test_db_connection():
    try:
        with pyodbc.connect(conn_string) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                return jsonify({'message': 'Database connection successful', 'result': result[0]})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)'''

