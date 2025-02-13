
from flask import Flask, redirect, url_for, session, request, render_template
import msal
import requests
from dotenv import load_dotenv
import os

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
    session['state'] = 'random_state'  # Use a random state for security
    auth_url = _build_auth_url(scopes=SCOPE, state=session['state'])
    print("Authorization URL:", auth_url)  # Debugging
    return redirect(auth_url)

# Callback route after Microsoft 365 login
@app.route('/auth/callback')
def authorized():
    print("Callback route called")  # Debugging
    try:
        if request.args.get('state') != session.get('state'):
            print("State mismatch")  # Debugging
            return redirect(url_for('index'))  # Prevent CSRF attacks

        # Get the authorization code from the request
        code = request.args.get('code')
        if not code:
            print("Authorization code not found")  # Debugging
            return redirect(url_for('index'))

        # Get the access token
        token = _get_token_from_code(code)
        if not token:
            print("Failed to get access token")  # Debugging
            return redirect(url_for('index'))

        # Get user info from Microsoft Graph
        user_info = _get_user_info(token)
        if not user_info:
            print("Failed to get user info")  # Debugging
            return redirect(url_for('index'))

        # Store user info in session
        session['user'] = user_info
        return redirect(url_for('success'))

    except Exception as e:
        print(f"Error in callback route: {e}")  # Debugging
        return redirect(url_for('index'))

# Success page after login
@app.route('/success')
def success():
    print("Success route called")  # Debugging
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
        # Initialize the MSAL client
        client = msal.ConfidentialClientApplication(
            CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)

        # Acquire the token using the authorization code
        result = client.acquire_token_by_authorization_code(
            code, scopes=SCOPE, redirect_uri=REDIRECT_URI)

        # Check if the token was acquired successfully
        if "access_token" in result:
            print("Access token acquired successfully")  # Debugging
            return result["access_token"]
        else:
            print("Failed to acquire access token. Response:", result)  # Debugging
            return None

    except Exception as e:
        print(f"Error acquiring token: {e}")  # Debugging
        return None

# Helper function to get user info from Microsoft Graph
def _get_user_info(token):
    graph_data = requests.get(
        'https://graph.microsoft.com/v1.0/me',
        headers={'Authorization': 'Bearer ' + token}).json()
    return graph_data

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
