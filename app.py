from flask import Flask, render_template, redirect, url_for, session, request
import msal
import requests
import os

app = Flask(__name__, template_folder="docs", static_folder="docs")

# Azure AD Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_URI = "https://your-azure-app.azurewebsites.net/auth/callback"
SCOPES = ["User.Read"]

# MSAL Client
def get_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    msal_app = get_msal_app()
    auth_url = msal_app.get_authorization_request_url(SCOPES, redirect_uri=REDIRECT_URI)
    return redirect(auth_url)

@app.route("/auth/callback")
def callback():
    if "error" in request.args:
        return render_template("error.html", error=request.args["error"], description=request.args.get("error_description", ""))

    if "code" in request.args:
        msal_app = get_msal_app()
        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"], SCOPES, redirect_uri=REDIRECT_URI
        )
        
        if "access_token" in result:
            session["user"] = result
            return redirect(url_for("profile"))

    return render_template("error.html", error="Login failed")

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))

    token = session["user"]["access_token"]
    user_info = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {token}"}
    ).json()

    return render_template("admin-view-profile.html", user=user_info)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
