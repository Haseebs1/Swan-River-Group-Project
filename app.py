from flask import Flask, redirect, url_for, session, request, render_template
from flask_session import Session
from requests_oauthlib import OAuth2Session
import os

# Allow insecure transport during development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__, template_folder='docs')
app.secret_key = 'swanRiver'  # Replace with a real secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Azure AD configuration
CLIENT_ID = "920e0dcb-6b9b-4ae1-8038-8b57c277dec3"  # Replace with your Azure AD app's Client ID
CLIENT_SECRET = "Kxb8Q~PV~cRSKJYeVjLi9YFWoFFjhsNWT4P.Ydcb"  # Replace with your Azure AD app's Client Secret
TENANT_ID = "170bbabd-a2f0-4c90-ad4b-0e8f0f0c4259"  # Replace with your Azure AD Tenant ID
AUTHORITY = f"https://login.microsoftonline.com/170bbabd-a2f0-4c90-ad4b-0e8f0f0c4259"
REDIRECT_URI= "/login/authorized"  # Must match the redirect URI in Azure AD

SCOPE = ['User.Read', 'Files.ReadWrite', 'email', 'openid', 'profile']

# OAuth2 session
oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login')
def login():
    authorization_url, state = oauth.authorization_url(f'{AUTHORITY}/oauth2/v2.0/authorize')
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/login/authorized')
def authorized():
    try:
        token = oauth.fetch_token(
            f'{AUTHORITY}/oauth2/v2.0/token',
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth_token'] = token

        # Fetch user info
        graph_client = OAuth2Session(CLIENT_ID, token=token)
        user_info = graph_client.get('https://graph.microsoft.com/v1.0/me').json()
        session['user_name'] = user_info['displayName']
        session['user_email'] = user_info['mail']  # Store user email in session

        # Check if the user is an admin based on email domain
        user_email = session.get('user_email', '').lower()
        is_admin = user_email.endswith('@example.com')  # Replace with your organization's domain

        # Redirect based on user role
        if is_admin:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('basic_user_home'))

    except Exception as e:
        print("Error during authorization:", str(e))  # Debug: Print the error
        return "Internal Server Error"

@app.route('/admin')
def admin():
    if 'oauth_token' not in session:
        return redirect(url_for('home'))  # Redirect to login if not authenticated
    user_name = session.get('user_name', 'Guest')
    return render_template('admin.html', user_name=user_name)

@app.route('/basic_user_home')
def basic_user_home():
    if 'oauth_token' not in session:
        return redirect(url_for('home'))  # Redirect to login if not authenticated
    user_name = session.get('user_name', 'Guest')
    return render_template('basic_user_home.html', user_name=user_name)

@app.route('/view_profile')
def view_profile():
    if 'oauth_token' not in session:
        return redirect(url_for('home'))  # Redirect to login if not authenticated
    user_name = session.get('user_name', 'Guest')
    user_email = session.get('user_email', 'guest@example.com')
    return render_template('basic_user_view.html', user_name=user_name, user_email=user_email)

@app.route('/edit_profile')
def edit_profile():
    if 'oauth_token' not in session:
        return redirect(url_for('home'))  # Redirect to login if not authenticated
    user_name = session.get('user_name', 'Guest')
    user_email = session.get('user_email', 'guest@example.com')
    return render_template('basic_user_edit.html', user_name=user_name, user_email=user_email)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'oauth_token' not in session:
        return redirect(url_for('home'))  # Redirect to login if not authenticated
    user_name = session.get('user_name', 'Guest')
    user_email = request.form.get('email')

    # Update the user email in the session
    session['user_email'] = user_email

    # Here you can add code to update the user profile in the database or any other storage

    return redirect(url_for('basic_user_home'))

@app.route('/view_emails')
def view_emails():
    if 'oauth_token' not in session:
        return redirect(url_for('home'))  # Redirect to login if not authenticated

    token = session.get('oauth_token')
    graph_client = OAuth2Session(CLIENT_ID, token=token)

    # Fetch email info
    response = graph_client.get('https://graph.microsoft.com/v1.0/me/messages').json()
    print("Response from Graph API:", response)  # Debug: Print the full response

    email_list = []
    if 'value' in response:
        email_list = [email['subject'] for email in response['value']]  # Example: Fetch email subjects
    else:
        print("Key 'value' not found in the response")

    return render_template('emails.html', emails=email_list)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)


