from flask import Flask, make_response, jsonify, redirect, request
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from datetime import timezone

import os
import requests
import jwt
import datetime

# -----------------------------
# A backend microservice to authenticate users with OAuth 2.0
# -----------------------------
PORT = 7001
DEBUG_MODE = True

app = Flask(__name__)
load_dotenv()

# Stand-in for REDIS database in theory 
SAVED_USER_INFO = {}

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"
CALLBACK_URL = os.getenv("CALLBACK_URL")
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET") 

# App specific
FRONTEND_URL = os.getenv("FRONTEND_URL")

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return "Auth Microservice Running"

@app.route("/login")
def login():
    """
    Redirects to Auth0 page for that specific client type
    """
    client_app = request.args.get("app-type", "invalid_entry")

    # Redirect user to Auth0 login page
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK_URL, # Must match the callback URL client
        "scope": "openid profile email",
        "state": f"app-type={client_app}",
        "prompt": "select_account"
    }
    auth_request = requests.Request("GET", AUTH_URL, params=params).prepare()
    return redirect(auth_request.url)

@app.route("/callback")
def callback():
    """
    'code' is unique 1 time code and provides access to exchange for token to auth0
        - Exchanged for access token
    Backend uses access token to retrieve user info
    Generates JWT token using access token from helper function, sends to client
    NOTE: JWT protects against CSRF/replay attacks (capturing callback url) or reusing login attempts
    """
    code = request.args.get("code")
    state = request.args.get("state") # defined in login request parameters
    client_app = state.split("=")[1] # grabs the type of app that's running
    if not code:
        return jsonify({"success": False, "error": "No code returned"}), 400

    token = exchange_code_for_token(code)
    user_info = exchange_token_for_user_info(token)

    if isinstance(user_info, tuple):
        user_info = user_info[0]
    
    # Save user info for later retrieval rather than request from Auth0 again
    # SAVED_USER_INFO[user_info["sub"]] = user_info

    # Retrieve private key 
    with open("private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Create JWT, encodes the user_info sub 
    # which is decoded in the microservice to retrieve the rest of the user info
    token = create_private_jwt(user_info, private_key)
    
    if client_app == "CLI":
        return handle_jwt_CLI(token)
    elif client_app == "Flask":
        return handle_jwt_flask(token)
    else:
        return jsonify({"success": False, "error": "Unknown client app"}), 400

@app.route("/verify-user")
def verify_user():
    """
    Verifies the user's JWT to authorize user on system
    """
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"success": False, "error": "Authorization header missing"}), 401

    # decode JWT

    with open("public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        user_info = jwt.decode(token, public_key, algorithms=["RS256"])
        print("User info success")
    except jwt.ExpiredSignatureError:
        print("Expired JWT")
        return jsonify({"success": False, "error": "JWT expired"}), 401
    except jwt.InvalidTokenError:
        print("Invalid JWT")
        return jsonify({"success": False, "error": "Invalid JWT"}), 401

    # if authenticated, return JSON with user info, otherwise error
    return jsonify({
        "success": True,
        "message": f"Hello, {user_info.get('name')}! You are authenticated.",
        "user_info": user_info
    })

# -----------------------------
# HELPERS
# -----------------------------

def exchange_code_for_token(code):
    """
    Exchanges an authorization code for an access token
    """
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": CALLBACK_URL,
        "scope": "openid profile email"
    }
    # Sends POST request with code for token 
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_resp = requests.post(TOKEN_URL, data=data, headers=headers)
    if not token_resp.ok:
        return {"success": False, "error": f"Token exchange failed: {token_resp.text}"}, 400

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return {"success": False, "error": "Missing access token"}, 400

    return access_token

def exchange_token_for_user_info(access_token):
    """
    Exchanges an access token for user info from Auth0 using /userinfo
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(USERINFO_URL, headers=headers)
    if not user_resp.ok:
        return {"success": False, "error": f"Failed to fetch user info: {user_resp.text}"}, 400

    return user_resp.json()

def handle_jwt_CLI(token):
    """
    Render the JWT token to give to the front end CLI app
    """
    # Instead of JSON, render a simple HTML page with the token
    return f"""
    <html>
        <body>
            <h1>CLI JWT</h1>
            <p>Copy this token into your CLI:</p>
            <textarea style="width:100%;height:200px;">{token}</textarea>
        </body>
    </html>
    """

def handle_jwt_flask(token):
    """
    Render front end URL page with JWT token inside cookie
    """
    response = make_response(redirect(FRONTEND_URL))
    response.set_cookie(
        "jwt_calorie_counter_profile", token, httponly=True, secure=False  # secure=True in production (HTTPS)
    )
    return response

def create_private_jwt(user_info, private_key, expires_minutes=10):
    """
    Creates a signed JWT with user info using RS256 (private/public key).
    """
    payload = {
        "sub": user_info["sub"],
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "exp": datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(minutes=expires_minutes)
    }
    # Change algorithm to RS256 and use private key
    token = jwt.encode(payload, private_key, algorithm="RS256")
    # user_info = jwt.decode(token, public_key, algorithms=["RS256"])
    return token

# Initialize application
if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG_MODE)
