import os
from flask import Flask, redirect, request, jsonify, make_response
import requests
from dotenv import load_dotenv
import jwt
import datetime
from cryptography.hazmat.primitives import serialization

# -----------------------------
# A backend microservice to authenticate users with OAuth 2.0
# -----------------------------

app = Flask(__name__)

load_dotenv()
app.secret_key = os.getenv("FLASK_SECRET_KEY")
ENV = os.getenv("ENV", "dev")  # dev | prod
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
CALLBACK_URL = os.getenv("CALLBACK_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
JWT_SHARED_SECRET = os.getenv("JWT_SHARED_SECRET")
AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"

# -----------------------------
# Helper to select Auth0 credentials per client
# -----------------------------
def get_client_credentials(client_app):
    if client_app == "CLI":
        return {
            "CLIENT_ID": os.getenv("CLI_CLIENT_ID"),
            "CLIENT_SECRET": os.getenv("CLI_CLIENT_SECRET"),
        }
    else: # Flask by default
        return {
            "CLIENT_ID": os.getenv("FLASK_CLIENT_ID"),
            "CLIENT_SECRET": os.getenv("FLASK_CLIENT_SECRET"),
        }

# -----------------------------
# Helper to screate a signed jwt to send user info to CLI
# -----------------------------
def create_shared_jwt(user_info, secret_key, expires_minutes=10):
    """
    Creates a signed JWT with user info.
    """
    payload = {
        "sub": user_info["sub"],
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

# -----------------------------
# Helper to screate a signed jwt to send user info to front end
# -----------------------------
def create_private_jwt(user_info, private_key, expires_minutes=10):
    """
    Creates a signed JWT with user info using RS256 (private/public key).
    """
    payload = {
        "sub": user_info["sub"],
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes)
    }
    # Change algorithm to RS256 and use private key
    token = jwt.encode(payload, private_key, algorithm="RS256")
    return token


# -----------------------------
# Helper to select Auth0 credentials per client
# -----------------------------
def exchange_code_and_login(
    code,
    token_url,
    client_id,
    client_secret,
    redirect_uri,
    userinfo_url=USERINFO_URL
):
    """
    Exchanges an authorization code for an access token,
    fetches user info from Auth0 using /userinfo,
    and optionally stores minimal user info in session (cookie) for Flask.
    """

    # ---- Exchange code for tokens ----
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email"
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_resp = requests.post(token_url, data=data, headers=headers)
    if not token_resp.ok:
        return {"success": False, "error": f"Token exchange failed: {token_resp.text}"}, 400

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return {"success": False, "error": "Missing access token"}, 400

    # ---- Fetch user info from Auth0 ----
    headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(userinfo_url, headers=headers)
    if not user_resp.ok:
        return {"success": False, "error": f"Failed to fetch user info: {user_resp.text}"}, 400

    user_info = user_resp.json()

    return user_info


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
    client_app = request.args.get("app", "invalid_entry")
    creds = get_client_credentials(client_app)

    # Redirect user to Auth0 login page
    params = {
        "response_type": "code",
        "client_id": creds["CLIENT_ID"],
        "redirect_uri": CALLBACK_URL,
        "scope": "openid profile email",
        "state": f"app={client_app}",
        "prompt": "select_account"
    }
    auth_request = requests.Request("GET", AUTH_URL, params=params).prepare() # AUTH_URL would be same for each user type
    # Each user has a 1 time generated auth_request that can be used once. 
    # Protects against CSRF/replay attacks (capturing callback url) or reusing login attempts
    return redirect(auth_request.url)

@app.route("/callback")
def callback():
    """
    'code' is unique 1 time code and provides access to exchange for JWT token
    """
    code = request.args.get("code")
    state = request.args.get("state")
    client_app = state.split("=")[1]
    creds = get_client_credentials(client_app)

    if not code:
        return jsonify({"success": False, "error": "No code returned"}), 400

    user_info = exchange_code_and_login(
        code=code,
        token_url=TOKEN_URL,
        client_id=creds["CLIENT_ID"],
        client_secret=creds["CLIENT_SECRET"],
        redirect_uri=CALLBACK_URL
    )
    
    if client_app == "CLI":
        # Ensure user_info is a dict
        if isinstance(user_info, tuple):
            user_info = user_info[0]
            print("DEBUG user_info raw:", user_info)
            print("Keys:", list(user_info.keys()))

        # Extract fields
        email = user_info.get("email")
        name = user_info.get("name")
        sub = user_info.get("sub")
        print(email, name, sub)

        # Create JWT
        token = create_shared_jwt(user_info, JWT_SHARED_SECRET)

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

    elif client_app == "Flask":
        # Create JWT
        with open("private.pem", "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        token = create_private_jwt(user_info, private_key)
        response = make_response(redirect(FRONTEND_URL))
        response.set_cookie(
            "jwt", token, httponly=True, secure=False  # secure=True in production (HTTPS)
        )
        return response

    else:
        return jsonify({"success": False, "error": "Unknown client app"}), 400

@app.route("/protected-endpoint")
def protected():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "error": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(" ")[1]

    try:
        user_info = jwt.decode(token, JWT_SHARED_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "error": "JWT expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "error": "Invalid JWT"}), 401

    return jsonify({
        "success": True,
        "message": f"Hello, {user_info.get('name')}! You are authenticated.",
        "user_info": user_info
    })

@app.route("/userinfo")
def userinfo():
    """
    Verifies the user's JWT to authorize user on system
    """
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"success": False, "error": "Authorization header missing"}), 401

    headers = {"Authorization": token}
    resp = requests.get(USERINFO_URL, headers=headers)
    return jsonify(resp.json())

if __name__ == "__main__":
    app.run(port=7001, debug=True)

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
