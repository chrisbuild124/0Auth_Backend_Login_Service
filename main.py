from flask import Flask, redirect, request, jsonify, make_response, g
from dotenv import load_dotenv
from auth0_facilitator import auth0
import os


PORT = 5005
app = Flask(__name__)
DOMAIN = f'http://localhost:{PORT}'

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"

load_dotenv()

# Receive a POST request a the flask domain
@app.route('/auth', methods=['POST'])
def auth():
    # Get app type from request
    data = request.json
    app_type = data['app-type']

    if app_type == 'CLI':
        return jsonify({'login-url': DOMAIN + '/login'}), 200
    elif app_type == 'Web':
        return jsonify({'error': 'App-type not supported'}), 200
    else:
        return jsonify({'error': 'App-type not supported'}), 400
    

# Handle the auth0 stuff

@app.before_request
def store_request_response():
    """Make request/response available for Auth0 SDK"""
    g.store_options = {"request": request}

@app.route('/login')
async def login():
    """Redirect to Auth0 login"""
    authorization_url = await auth0.start_interactive_login({}, g.store_options)
    return redirect(authorization_url)

@app.route('/callback')
async def callback():
    """Handle Auth0 callback after login"""
    try:
        result = await auth0.complete_interactive_login(str(request.url), g.store_options)
        return redirect(DOMAIN + '/success')
    except Exception as e:
        return f"Authentication error: {str(e)}", 400
    
@app.route('/success')
async def success():
    """When login works, go here and print the user-id"""
    user = await auth0.get_user(g.store_options)
    return f'Logged in successfully with user: {user['sub']}, return to the app.'

if __name__ == "__main__":
    app.run(port=PORT, debug=True)