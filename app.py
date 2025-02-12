from flask import Flask, redirect, url_for, session, render_template, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import msal
import uuid
from requests_oauthlib import OAuth2Session

app = Flask(__name__, static_folder="docs", template_folder="docs")
app.secret_key = "your_secret_key"  # Replace with a secure secret key

# Home route
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))  # Redirect authenticated users to admin
    return render_template("index.html")

# Azure AD configuration
CLIENT_ID = "920e0dcb-6b9b-4ae1-8038-8b57c277dec3"  # Replace with your Azure AD app's Client ID
CLIENT_SECRET = "Kxb8Q~PV~cRSKJYeVjLi9YFWoFFjhsNWT4P.Ydcb"  # Replace with your Azure AD app's Client Secret
TENANT_ID = "170bbabd-a2f0-4c90-ad4b-0e8f0f0c4259"  # Replace with your Azure AD Tenant ID
AUTHORITY = f"https://login.microsoftonline.com/170bbabd-a2f0-4c90-ad4b-0e8f0f0c4259"
REDIRECT_URI= "login/authorized"  # Must match the redirect URI in Azure AD
SCOPE = ["User.Read"]  # Permissions to request

# OAuth2 session
oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

# Microsoft authentication route
@app.route('/login')
def login():
    authorization_url, state = oauth.authorization_url(f'{AUTHORITY}/oauth2/v2.0/authorize')
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/login/authorized')
def authorized():
    try:
        app.logger.info("Starting OAuth token fetch")
        token = oauth.fetch_token(
            f'{AUTHORITY}/oauth2/v2.0/token',
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        session['oauth_token'] = token
        app.logger.info("Token fetched successfully")

        # Fetch user info
        graph_client = OAuth2Session(CLIENT_ID, token=token)
        user_info = graph_client.get('https://graph.microsoft.com/v1.0/me').json()
        app.logger.info("User info fetched: %s", user_info)
        session['user_name'] = user_info['displayName']
        session['user_email'] = user_info['mail']  # Store user email in session

        # Always redirect to admin route
        return redirect(url_for('admin'))

    except Exception as e:
        app.logger.error("Error during authorization: %s", str(e))  # Log the error
        return "Internal Server Error", 500


# Admin route (protected)
@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

# Basic user home route
@app.route('/basic_user_home')
@login_required
def basic_user_home():
    user_name = session.get('user_name', 'Guest')
    return render_template('basic_user_home.html', user_name=user_name)

# User profile routes
@app.route('/view_profile')
@login_required
def view_profile():
    user_name = session.get('user_name', 'Guest')
    user_email = session.get('user_email', 'guest@example.com')
    return render_template('basic_user_view.html', user_name=user_name, user_email=user_email)

@app.route('/edit_profile')
@login_required
def edit_profile():
    user_name = session.get('user_name', 'Guest')
    user_email = session.get('user_email', 'guest@example.com')
    return render_template('basic_user_edit.html', user_name=user_name, user_email=user_email)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user_name = session.get('user_name', 'Guest')
    user_email = request.form.get('email')

    # Update the user email in the session
    session['user_email'] = user_email

    # Here you can add code to update the user profile in the database or any other storage

    return redirect(url_for('basic_user_home'))

@app.route('/view_emails')
@login_required
def view_emails():
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

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

# Helper functions for Microsoft authentication
def _build_auth_url(scopes=None, state=None):
    return msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY
    ).get_authorization_request_url(scopes, state=state, redirect_uri=url_for("authorized", _external=True))

def _acquire_token_by_auth_code_flow(request_args):
    cache = msal.SerializableTokenCache()
    app = msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET, token_cache=cache
    )
    result = app.acquire_token_by_authorization_code(
        request_args["code"], scopes=SCOPE, redirect_uri=url_for("authorized", _external=True)
    )
    return result


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)


