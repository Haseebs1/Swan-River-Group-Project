from flask import Flask, redirect, url_for, session, request, render_template
import msal
import pyodbc
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
SERVER = os.getenv('AZURE_SQL_SERVER')
DATABASE = os.getenv('AZURE_SQL_DATABASE')
USERNAME = os.getenv('AZURE_SQL_USERNAME')
PASSWORD = os.getenv('AZURE_SQL_PASSWORD')
DRIVER = '{ODBC Driver 18 for SQL Server}'  # Use the appropriate driver

# Connection string
connection_string = f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Function to get a database connection
def get_db_connection():
    try:
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

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

@app.route('/admin-edit-profile')
def admin_edit_profile():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-edit-profile.html', user_name=user_name)

@app.route('/admin-create-user')
def admin_create_user():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-create-user.html', user_name=user_name)

@app.route('/admin-view-user')
def admin_view_user():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-view-user.html', user_name=user_name)

@app.route('/admin-update-user')
def admin_update_user():
    if not session.get('user'):
        return redirect(url_for('index'))
    user_name = session['user']['displayName']
    return render_template('admin-update-user.html', user_name=user_name)

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

# Example route to fetch data from the database
@app.route('/data')
def fetch_data():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM your_table_name")  # Replace with your table name
        rows = cursor.fetchall()
        conn.close()
        return render_template('data.html', rows=rows)
    else:
        return "Failed to connect to the database."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
