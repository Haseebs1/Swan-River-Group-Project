from flask import Flask, redirect, url_for, session, request, render_template, jsonify
import msal
import requests
import os
import pyodbc
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
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


# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/azure_login')
def azure_login():
    session['state'] = 'random_state'
    auth_url = _build_auth_url(scopes=SCOPE, state=session['state'])
    return redirect(auth_url)

@app.route('/auth/callback')
def authorized():
    code = request.args.get('code')
    if not code:
        return redirect(url_for('index'))
    token = _get_token_from_code(code)
    user_info = _get_user_info(token)
    
    # Check if the user exists in the database
    user = User.query.filter_by(email=user_info['mail']).first()
    if not user:
        # Create a new user if not found
        user = User(name=user_info['displayName'], email=user_info['mail'])
    user.status = "active"  # Set the status to active
    db.session.add(user)
    db.session.commit()
    
    session['user'] = user_info
    return redirect(url_for('basic_user_home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/basic_user_home')
def basic_user_home():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template('basic_user_home.html', user_name=session['user']['displayName'])

@app.route('/basic_user_view')
def basic_user_view():
    if 'user' not in session:
        return redirect(url_for('index'))
    user = session['user']
    return render_template("basic_user_view.html", user=user)


@app.route('/basic_user_edit')
def basic_user_edit():
    return render_template("basic_user_edit.html")

@app.route('/user/profile')
def user_profile():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401
    user = User.query.filter_by(email=session['user'].get('email')).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"name": user.name, "email": user.email, "role": user.role, "status": user.status})


@app.route('/user/profile/update', methods=['PUT'])
def update_user_profile():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401
    user = User.query.filter_by(email=session['user'].get('email')).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = request.get_json()
    user.name = data.get("name", user.name)
    db.session.commit()
    return jsonify({"message": "Profile updated successfully!"})

# Helper functions
def _build_auth_url(scopes=None, state=None):
    return msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY).get_authorization_request_url(
        scopes, state=state, redirect_uri=REDIRECT_URI)

def _get_token_from_code(code):
    client = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
    result = client.acquire_token_by_authorization_code(code, scopes=SCOPE, redirect_uri=REDIRECT_URI)
    return result.get("access_token")

def _get_user_info(token):
    user_info = requests.get('https://graph.microsoft.com/v1.0/me', headers={'Authorization': 'Bearer ' + token}).json()
    user_info['role'] = 'basicuser'
    user_info['status'] = 'active'
    return user_info

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

