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
#     private_key = """-----BEGIN PRIVATE KEY-----
# MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDd5gBEK+gB0rpv
# CUQ75wANJV/lzMIO0J/k4TGxSGtPd/eMBbV8Tjl82Hklm1v9DehBHk0u3DBQUGjR
# y5NvtOWLJnPtnDG1cct4B854XifLm1mE8OI99O5kIiPt8BnjLKE7u/J55VGmPY16
# RD7iMOByGro3bp6hqW3383Ol+qLiaxE/qfKc2It86Y7alzAHUyi/fOLm8dhDzwza
# z0DjpozTR84dPBPXS7MwtMrbVT+kPclEAQw3sOiIqxPWE+nsBgxLFIFyU4Q3lx2/
# jubGI3pYA4M1ulOvyXA6T3k/Trwtl+9SGPaGqUvyBFk6ZMdUd9Tg8IIB/Ntk4GdN
# 0VWf7s0nAgMBAAECggEAGnzNBVY0YJtV89EoWvotEGSouNajR39xxrF27BGX9al9
# XDKGQmtYA2YXt/x+k4tocPV8Ax73iW6/xGNHmyr9x4l0hyWA7YbC4fYUmFus5moJ
# 2ouihgDJwBwvK8TgYjS+nlHGFPThtTVdwP2KgBeTgytblShYOTXvUYy2/lYXwW0L
# fi9sCoVWvPwiEPeckyWa+WtFM4iMtci3lnuWmYDXrqHj5hRbAQp2Vm8DYToOwHJV
# DJJ8uNv5fdwjwp9Q23bjGSLutMNXAAKF7sFTWZAPKcw6wE9Jx/BOKdxXAo6+qs6/
# tmlMMjBnfqQGgAgx8zAS0BJquhuD5VDiGr8n6y/CQQKBgQDyghjm51NgFy+a0/lH
# bwgJDenRuGVHWlR7FZiYgDIY+rdU5Z+NOYQQfeBaHZ85ROJH9tf0l/Bz/AOor3Bd
# WwQn26kAYSqga5bH6skW24Qssiv0KePTAI/IB1pOhyZgUbfZ7ZJ5X7mON9aSdt8W
# zO7i8StWRjkFVH2t4mGWOlMloQKBgQDqPl8A2LgDoIkgl7nFji0DhHkH/iiNsbP8
# 5vqbQ17yX8tC3RamLpnf/nnujptbA1WyW5tjPOcGgQQrvVSaYhbqW4XRxkDA3nDG
# 4i5cqokG9/dp/ClsIFltv58sIT4UiQEmiOoD9YlK5a9LIWrbQSUSQ19ffFaBUHds
# wmiPLudtxwKBgQDvzK+dHF+4pBTB0Bwug995PJXaeLFFdlAVigxjuFhRlRHWVF2K
# Q7aQrDg+RA5fjfsH2FJBnkD6H9jqY9kDp22bkD00j+Cb0ue9djA0dwrjO6f0/7s1
# uddzn7mv7zqGgif/yklN1ddhh1uZZwxAupL6PCpzXGskFyFT4YhIChKQIQKBgDs9
# Ns2CAVd5e/RwKp0Zjay8DdfFoP/klv44c9xcN2DYdREd1KKGWofZVYDNM+DagQuw
# OyXnuw1cB3AAW6sHb4ApUThyCOI93wuNG+h3gFvwzfNRwDAGJlepBFomtgp/c3kJ
# WxVRPT1hxOkdNGbqnLN3smD1kvL1JJ6us76yP/j1AoGALWeK1ih2+6wVFCUzJn7Y
# qNzcM6k/D8SaN/GwyaAZPIvBZSd2KqhKIlkRzgUX/pv+sCg1nnTU9SyCG6f+KXKT
# cA+Xs7mZgxg8L6Om9JwzCTVUNJhRERM15cPW4Xfuo9a0rZUPEKIN5p7cdSsq5DGk
# xFWbbkothcVbqTPha/l9NHc=
# -----END PRIVATE KEY-----"""

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
#     public_key = """-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzcfDW41w7kOPUCo1xwiK
# ceR5t9ma05HQlLshCPDEbQFwu//fvwz/ZmcpZM4FqtHbhLMjBMotR2zptUDMHaW0
# mLUaEgXGpjR85Tptqk4pe2HALKzMIOTNieoyrazjndw8GfOafOENHkH+7IM3R8Tg
# VAjI1JMyFh//6l7mf2P/mFDVV/ZVKvB4/H1XiMhlEL+jlyKi3cgVuxh2ERV9K28R
# bsGN3m+VjhOEPbh0yBgGgJtdJCAFT43+6e4EtTWRY6Eg8csSg7DyBeX4crUt+2RU
# hyDo1grtOxy13PbekA7WusnOos9JZugVwnrWsKHdkCggJRaS47Dsw/wbw6fe4LRW
# oQIDAQAB
# -----END PUBLIC KEY-----"""
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

    # headers = {"Authorization": token}
    # resp = requests.get(USERINFO_URL, headers=headers)
    # return jsonify(resp.json())

# Return the user information 
# def get_user_info(sub):
#     return SAVED_USER_INFO.get(sub, None)

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
    # Ensure user_info is a dict
    # if isinstance(user_info, tuple):
    #     user_info = user_info[0]
    #     print("DEBUG user_info raw:", user_info)
    #     print("Keys:", list(user_info.keys()))

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

# -----------------------------
# Helper to create a signed jwt to send user info to front end
# -----------------------------
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
#     public_key = """-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzcfDW41w7kOPUCo1xwiK
# ceR5t9ma05HQlLshCPDEbQFwu//fvwz/ZmcpZM4FqtHbhLMjBMotR2zptUDMHaW0
# mLUaEgXGpjR85Tptqk4pe2HALKzMIOTNieoyrazjndw8GfOafOENHkH+7IM3R8Tg
# VAjI1JMyFh//6l7mf2P/mFDVV/ZVKvB4/H1XiMhlEL+jlyKi3cgVuxh2ERV9K28R
# bsGN3m+VjhOEPbh0yBgGgJtdJCAFT43+6e4EtTWRY6Eg8csSg7DyBeX4crUt+2RU
# hyDo1grtOxy13PbekA7WusnOos9JZugVwnrWsKHdkCggJRaS47Dsw/wbw6fe4LRW
# oQIDAQAB
# -----END PUBLIC KEY-----"""
    # Change algorithm to RS256 and use private key
    token = jwt.encode(payload, private_key, algorithm="RS256")
    # user_info = jwt.decode(token, public_key, algorithms=["RS256"])
    return token

# Initialize application
if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG_MODE)

# -----------------------------
# import os
# from flask import Flask, redirect, request, jsonify, make_response
# import requests
# from dotenv import load_dotenv
# import jwt
# import datetime
# from cryptography.hazmat.primitives import serialization

# -----------------------------
# A backend microservice to authenticate users with OAuth 2.0
# -----------------------------

# app = Flask(__name__)

# load_dotenv()
# app.secret_key = os.getenv("FLASK_SECRET_KEY")
# ENV = os.getenv("ENV", "dev")  # dev | prod
# AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
# CALLBACK_URL = os.getenv("CALLBACK_URL")
# FRONTEND_URL = os.getenv("FRONTEND_URL")
# JWT_SHARED_SECRET = os.getenv("JWT_SHARED_SECRET")
# AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
# TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
# USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"

# -----------------------------
# Helper to select Auth0 credentials per client
# -----------------------------
# def get_client_credentials(client_app):
#     if client_app == "CLI":
#         return {
#             "CLIENT_ID": os.getenv("CLI_CLIENT_ID"),
#             "CLIENT_SECRET": os.getenv("CLI_CLIENT_SECRET"),
#         }
#     else: # Flask by default
#         return {
#             "CLIENT_ID": os.getenv("FLASK_CLIENT_ID"),
#             "CLIENT_SECRET": os.getenv("FLASK_CLIENT_SECRET"),
#         }

# -----------------------------
# Helper to screate a signed jwt to send user info to CLI
# -----------------------------
# def create_shared_jwt(user_info, secret_key, expires_minutes=10):
#     """
#     Creates a signed JWT with user info.
#     """
#     payload = {
#         "sub": user_info["sub"],
#         "email": user_info.get("email"),
#         "name": user_info.get("name"),
#         "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes)
#     }
#     token = jwt.encode(payload, secret_key, algorithm="HS256")
#     return token

# -----------------------------
# Helper to screate a signed jwt to send user info to front end
# -----------------------------
# def create_private_jwt(user_info, private_key, expires_minutes=10):
#     """
#     Creates a signed JWT with user info using RS256 (private/public key).
#     """
#     payload = {
#         "sub": user_info["sub"],
#         "email": user_info.get("email"),
#         "name": user_info.get("name"),
#         "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes)
#     }
#     # Change algorithm to RS256 and use private key
#     token = jwt.encode(payload, private_key, algorithm="RS256")
#     return token


# -----------------------------
# Helper to select Auth0 credentials per client
# -----------------------------
# def exchange_code_and_login(
#     code,
#     token_url,
#     client_id,
#     client_secret,
#     redirect_uri,
#     userinfo_url=USERINFO_URL
# ):
#     """
#     Exchanges an authorization code for an access token,
#     fetches user info from Auth0 using /userinfo,
#     and optionally stores minimal user info in session (cookie) for Flask.
#     """

#     # ---- Exchange code for tokens ----
#     data = {
#         "grant_type": "authorization_code",
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "code": code,
#         "redirect_uri": redirect_uri,
#         "scope": "openid profile email"
#     }

#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     token_resp = requests.post(token_url, data=data, headers=headers)
#     if not token_resp.ok:
#         return {"success": False, "error": f"Token exchange failed: {token_resp.text}"}, 400

#     tokens = token_resp.json()
#     access_token = tokens.get("access_token")
#     if not access_token:
#         return {"success": False, "error": "Missing access token"}, 400

#     # ---- Fetch user info from Auth0 ----
#     headers = {"Authorization": f"Bearer {access_token}"}
#     user_resp = requests.get(userinfo_url, headers=headers)
#     if not user_resp.ok:
#         return {"success": False, "error": f"Failed to fetch user info: {user_resp.text}"}, 400

#     user_info = user_resp.json()

#     return user_info


# -----------------------------
# Routes
# -----------------------------
# @app.route("/")
# def home():
#     return "Auth Microservice Running"

# @app.route("/login")
# def login():
#     """
#     Redirects to Auth0 page for that specific client type
#     """
#     client_app = request.args.get("app", "invalid_entry")
#     creds = get_client_credentials(client_app)

#     # Redirect user to Auth0 login page
#     params = {
#         "response_type": "code",
#         "client_id": creds["CLIENT_ID"],
#         "redirect_uri": CALLBACK_URL,
#         "scope": "openid profile email",
#         "state": f"app={client_app}",
#         "prompt": "select_account"
#     }
#     auth_request = requests.Request("GET", AUTH_URL, params=params).prepare() # AUTH_URL would be same for each user type
#     # Each user has a 1 time generated auth_request that can be used once. 
#     # Protects against CSRF/replay attacks (capturing callback url) or reusing login attempts
#     return redirect(auth_request.url)

# @app.route("/callback")
# def callback():
#     """
#     'code' is unique 1 time code and provides access to exchange for JWT token
#     """
#     code = request.args.get("code")
#     state = request.args.get("state")
#     client_app = state.split("=")[1]
#     creds = get_client_credentials(client_app)

#     if not code:
#         return jsonify({"success": False, "error": "No code returned"}), 400

#     user_info = exchange_code_and_login(
#         code=code,
#         token_url=TOKEN_URL,
#         client_id=creds["CLIENT_ID"],
#         client_secret=creds["CLIENT_SECRET"],
#         redirect_uri=CALLBACK_URL
#     )
    
#     if client_app == "CLI":
#         # Ensure user_info is a dict
#         if isinstance(user_info, tuple):
#             user_info = user_info[0]
#             print("DEBUG user_info raw:", user_info)
#             print("Keys:", list(user_info.keys()))

#         # Extract fields
#         email = user_info.get("email")
#         name = user_info.get("name")
#         sub = user_info.get("sub")
#         print(email, name, sub)

#         # Create JWT
#         token = create_shared_jwt(user_info, JWT_SHARED_SECRET)

#         # Instead of JSON, render a simple HTML page with the token
#         return f"""
#         <html>
#             <body>
#                 <h1>CLI JWT</h1>
#                 <p>Copy this token into your CLI:</p>
#                 <textarea style="width:100%;height:200px;">{token}</textarea>
#             </body>
#         </html>
#         """

#     elif client_app == "Flask":
#         # Create JWT
#         with open("private.pem", "rb") as f:
#             private_key = serialization.load_pem_private_key(f.read(), password=None)
#         token = create_private_jwt(user_info, private_key)
#         response = make_response(redirect(FRONTEND_URL))
#         response.set_cookie(
#             "jwt", token, httponly=True, secure=False  # secure=True in production (HTTPS)
#         )
#         return response

#     else:
#         return jsonify({"success": False, "error": "Unknown client app"}), 400

# @app.route("/protected-endpoint")
# def protected():
#     auth_header = request.headers.get("Authorization", "")
#     if not auth_header.startswith("Bearer "):
#         return jsonify({"success": False, "error": "Missing or invalid Authorization header"}), 401

#     token = auth_header.split(" ")[1]

#     try:
#         user_info = jwt.decode(token, JWT_SHARED_SECRET, algorithms=["HS256"])
#     except jwt.ExpiredSignatureError:
#         return jsonify({"success": False, "error": "JWT expired"}), 401
#     except jwt.InvalidTokenError:
#         return jsonify({"success": False, "error": "Invalid JWT"}), 401

#     return jsonify({
#         "success": True,
#         "message": f"Hello, {user_info.get('name')}! You are authenticated.",
#         "user_info": user_info
#     })

# @app.route("/userinfo")
# def userinfo():
#     """
#     Verifies the user's JWT to authorize user on system
#     """
#     token = request.headers.get("Authorization")
#     if not token:
#         return jsonify({"success": False, "error": "Authorization header missing"}), 401

#     headers = {"Authorization": token}
#     resp = requests.get(USERINFO_URL, headers=headers)
#     return jsonify(resp.json())

# if __name__ == "__main__":
#     app.run(port=7001, debug=True)

# from flask import Flask, redirect, request, jsonify, make_response, g
# from dotenv import load_dotenv
# from auth0_facilitator import auth0
# import os


# PORT = 5005
# app = Flask(__name__)
# DOMAIN = f'http://localhost:{PORT}'

# AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
# AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
# TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
# USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"

# load_dotenv()

# # Receive a POST request a the flask domain
# @app.route('/auth', methods=['POST'])
# def auth():
#     # Get app type from request
#     data = request.json
#     app_type = data['app-type']

#     if app_type == 'CLI':
#         return jsonify({'login-url': DOMAIN + '/login'}), 200
#     elif app_type == 'Web':
#         return jsonify({'error': 'App-type not supported'}), 200
#     else:
#         return jsonify({'error': 'App-type not supported'}), 400
    

# # Handle the auth0 stuff

# @app.before_request
# def store_request_response():
#     """Make request/response available for Auth0 SDK"""
#     g.store_options = {"request": request}

# @app.route('/login')
# async def login():
#     """Redirect to Auth0 login"""
#     authorization_url = await auth0.start_interactive_login({}, g.store_options)
#     return redirect(authorization_url)

# @app.route('/callback')
# async def callback():
#     """Handle Auth0 callback after login"""
#     try:
#         result = await auth0.complete_interactive_login(str(request.url), g.store_options)
#         return redirect(DOMAIN + '/success')
#     except Exception as e:
#         return f"Authentication error: {str(e)}", 400
    
# @app.route('/success')
# async def success():
#     """When login works, go here and print the user-id"""
#     user = await auth0.get_user(g.store_options)
#     return f'Logged in successfully with user: {user['sub']}, return to the app.'

# if __name__ == "__main__":
#     app.run(port=PORT, debug=True)
