from flask import Flask, redirect, url_for, session, render_template, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import msal
import uuid

app = Flask(__name__, static_folder="docs", template_folder="docs")
app.secret_key = "your_secret_key"  # Replace with a secure secret key

# Azure AD configuration
CLIENT_ID = "920e0dcb-6b9b-4ae1-8038-8b57c277dec3"  # Replace with your Azure AD app's Client ID
CLIENT_SECRET = "Kxb8Q~PV~cRSKJYeVjLi9YFWoFFjhsNWT4P.Ydcb"  # Replace with your Azure AD app's Client Secret
TENANT_ID = "170bbabd-a2f0-4c90-ad4b-0e8f0f0c4259"  # Replace with your Azure AD Tenant ID
AUTHORITY = f"https://login.microsoftonline.com/170bbabd-a2f0-4c90-ad4b-0e8f0f0c4259"
REDIRECT_PATH = "/login/callback"  # Must match the redirect URI in Azure AD
SCOPE = ["User.Read"]  # Permissions to request

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)

# Dummy user class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Microsoft authentication route
@app.route("/login")
def login():
    print("Login route called")  # Debugging statement
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=SCOPE, state=session["state"])
    print("Auth URL:", auth_url)  # Debugging statement
    return redirect(auth_url)

# Callback route for Microsoft authentication
@app.route("/login/callback")
def authorized():
    if request.args.get("state") != session.get("state"):
        return redirect(url_for("home"))  # Invalid state, redirect to home
    if "error" in request.args:  # Authentication failed
        return f"Error: {request.args['error_description']}"
    if "code" in request.args:  # Authentication succeeded
        result = _acquire_token_by_auth_code_flow(request.args)
        if "error" in result:
            return f"Error: {result['error_description']}"
        user = User(result["id_token_claims"]["oid"])  # Create user from Azure AD ID
        login_user(user)
        return redirect(url_for("admin"))  # Redirect to admin page

# Admin route (protected)
@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

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

# Home route
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

