'''from flask import Flask, redirect, url_for, session, request, render_template
from flask_sqlalchemy import SQLAlchemy
import msal
import requests
import os
from dotenv import load_dotenv

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

# Azure SQL Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mssql+pyodbc://{os.getenv('AZURE_SQL_USERNAME')}:{os.getenv('AZURE_SQL_PASSWORD')}@"
    f"{os.getenv('AZURE_SQL_SERVER')}/{os.getenv('AZURE_SQL_DATABASE')}?"
    "driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__ = 'User'  # Explicitly sets table name to match table in Azure database

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

# Admin view profile page
@app.route('/admin-view-profile')
def admin_view_profile():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-view-profile.html', user_name=user_name)

# Admin edit profile page
@app.route('/admin-edit-profile')
def admin_edit_profile():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-edit-profile.html', user_name=user_name)

# Admin create user page
@app.route('/admin-create-user')
def admin_create_user():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-create-user.html', user_name=user_name)

# Admin view users page
@app.route('/admin-view-user')
def admin_view_user():
    if not session.get('user'):
        return redirect(url_for('index'))

    try:
        # Fetch all users from the database
        users = User.query.all()
        user_name = session['user']['displayName']
        return render_template('admin-view-user.html', user_name=user_name, users=users)

    except Exception as e:
        # Log any errors
        print(f"Error fetching users: {e}")
        return "An error occurred while fetching users.", 500

# Admin update user page
@app.route('/admin-update-user')
def admin_update_user():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-update-user.html', user_name=user_name)

# Admin delete user page
@app.route('/admin-delete-user')
def admin_delete_user():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-delete-user.html', user_name=user_name)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

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
    app.run(host='0.0.0.0', port=5000)'''

from flask import Flask
import pyodbc

app = Flask(__name__)

# Database connection details
server = "tcp:swan-river123.database.windows.net"
database = "Swan-River"
username = "swanriver"
password = "<Admin123>"
driver = "{ODBC Driver 18 for SQL Server}"

# Build connection string
conn_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Create connection
def get_db_connection():
    try:
        conn = pyodbc.connect(conn_string)
        return conn
    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")
        return None

@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User")  # Replace with your table name
        rows = cursor.fetchall()
        conn.close()
        return f"Fetched {len(rows)} rows from the database."
    else:
        return "Failed to connect to the database."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1433)
