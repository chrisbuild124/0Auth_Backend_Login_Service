from flask import Flask, redirect, request, jsonify, make_response, g
import requests
from dotenv import load_dotenv
from auth0_facilitator import auth0
import os


RECEIVE_PORT = 5005
SEND_PORT = 5006
app = Flask(__name__)
DOMAIN = f'http://localhost:{RECEIVE_PORT}'
DESTINATION = f'http://localhost:{SEND_PORT}'

# AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
# AUTH_URL = f"https://{AUTH0_DOMAIN}/authorize"
# TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
# USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"

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
        return f"Authentication error: {str(e)}. Try the link again.", 400
    
@app.route('/success')
async def success():
    """When login works, go here and print the user-id"""
    user = await auth0.get_user(g.store_options)

    # Send request with body of user_id to 
    result = requests.post(
        DESTINATION + '/auth',
        json={'user_id': f'{user['sub']}'}
    )

    return f'Logged in successfully with user: {user['sub']}, return to the app.'

if __name__ == "__main__":
    app.run(port=RECEIVE_PORT, debug=True)