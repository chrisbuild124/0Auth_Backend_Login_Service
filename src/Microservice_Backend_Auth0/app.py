from flask import Flask, make_response, jsonify, redirect, request
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from datetime import timezone
import os
import requests
import jwt
import datetime

# -----------------------------
# A backend microservice to authenticate users with Auth0 and
# generate JWT tokens for frontend applications (CLI and Web)
# -----------------------------
PORT = 7001
DEBUG_MODE = True

app = Flask(__name__)
load_dotenv()

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
    Redirects to Auth0 URL page for that specific client type
    """
    client_app = request.args.get("app-type", "invalid_entry") # URL parameters

    # Redirect user to Auth0 login page
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": CALLBACK_URL, # Must match the callback URL client
        "scope": "openid profile email", # Tells what parameters we want back from Auth0
        "state": client_app, # Sent directly back in callback
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
    Generates JWT token using user info & private key, sends to client
    """
    code = request.args.get("code", None)
    client_app = request.args.get("state", None)  # defined in login request parameters
    if not code:
        return jsonify({"success": False, "error": "No code returned", "error status code": 400})

    # Echange code for token
    token_object = exchange_code_for_token(code)
    if not token_object["success"]:
        return token_object["error"]
    # Exchange token for user info
    user_info = exchange_token_for_user_info(token_object["access_token"])
    if not user_info["success"]:
        return user_info["error"]

    # Retrieve private key and make jwt
    with open("private.pem", "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    token = create_private_jwt(user_info, private_key)
    
    if client_app == "CLI":
        return handle_jwt_CLI(token)
    elif client_app == "Flask":
        return handle_jwt_flask(token)
    else:
        return jsonify({"success": False, "error": "Unknown client app", "error status code": 400})

@app.route("/verify-user")
def verify_user():
    """
    Verifies the user's JWT to authorize user on system
    """
    token = request.headers.get("Authorization", None)
    if not token:
        return jsonify({"success": False, "error": "Authorization header missing", "error status code": 401})

    with open("public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    # decode JWT
    try:
        user_info = jwt.decode(token, public_key, algorithms=["RS256"])
        print("User info success")
    except jwt.ExpiredSignatureError:
        print("Expired JWT")
        return jsonify({"success": False, "error": "JWT expired", "error status code": 401})
    except jwt.InvalidTokenError:
        print("Invalid JWT")
        return jsonify({"success": False, "error": "Invalid JWT", "error status code": 401})

    # returns successful message
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
    Returns Python Dictionary
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
    headers = {"Content-Type": "application/x-www-form-urlencoded"} # String form
    res = requests.post(TOKEN_URL, data=data, headers=headers)
    if res.status_code not in (200, 201, 204):
        return {"success": False, "error": f"Token exchange failed, status code: {res.status_code}"}

    tokens = res.json()
    access_token = tokens.get("access_token", None)
    if not access_token:
        return {"success": False, "error": "Invalid token response from Auth0"}

    return {"success": True, "access_token": access_token}

def exchange_token_for_user_info(access_token):
    """
    Exchanges an access token for user info from Auth0 using /userinfo
    Returns Python dictionary
    """
    headers = {"Authorization": f"Bearer {access_token}"} # Bearer is Auth 2.0 protocol standard
    res = requests.get(USERINFO_URL, headers=headers)
    if res.status_code not in (200, 201, 204):
        return {"success": False, "error": f"Failed to fetch user info, status code: {res.status_code}"}
    
    response = res.json()
    response["success"] = True
    return response

def handle_jwt_CLI(token):
    """
    Render the JWT token to give to the front end CLI app
    """
    # Render a simple HTML page with the token
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
    Creates a signed JWT with user info using RS256 (private/public key)
    """
    payload = {
        "sub": user_info["sub"],
        "email": user_info.get("email", None),
        "name": user_info.get("name", None),
        "exp": datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(minutes=expires_minutes)
    }
    # Change algorithm to RS256 and use private key
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token

# Initialize application
if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG_MODE)
