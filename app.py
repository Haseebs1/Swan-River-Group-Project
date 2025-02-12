from flask import Flask, redirect, url_for, session, render_template, request
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Azure AD Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
REDIRECT_URI = "https://swanriver-hpchbdasddbqfxd4.centralus-01.azurewebsites.net/docs/admin.html"
SCOPE = "files.readwrite"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"

@app.route("/")
def index():
    if "user" in session:
        return render_template("index.html", user=session["user"])
    return render_template("index.html")

@app.route("/login")
def login():
    if "user" in session:
        return redirect(url_for("index"))
    
    # Construct the authorization URL
    auth_url = (
        f"https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize?"
        f"client_id={CLIENT_ID}&scope={SCOPE}&response_type=token&redirect_uri={REDIRECT_URI}"
    )
    return redirect(auth_url)

@app.route("/callback")
def callback():
    token = request.args.get("token")
    if token:
        session["user"] = token  # Here, you can store the user's information in the session
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

