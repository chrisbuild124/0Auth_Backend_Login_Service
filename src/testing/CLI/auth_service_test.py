from flask import Flask, request, jsonify
import requests

SEND_PORT=5005
RECEIVE_PORT=5006
DESTINATION=f'http://localhost:{SEND_PORT}/auth'
APP_TYPE='CLI'

app = Flask(__name__)

# Domain 'app-type': app-type
# 'Web', 'CLI'

result = requests.post(
    DESTINATION,
    json={'app-type': f'{APP_TYPE}'}
)

login_url = result.json()
print(login_url) # Should be the login URL to authenticate

# Need a way to get back the auth0 userID
# Tried making the main program a flask app as well just to listen for requests on the port
@app.route('/auth', methods=['POST'])
def auth():
    # Grab the json from the post
    data = request.json
    user_id = data['user_id']
    
    if user_id:
        print(user_id)
        return jsonify({'status': 'received user_id'}), 200
    else:
        return jsonify({'error': 'user_id not part of json body'}), 400


if __name__ == "__main__":
    app.run(port=RECEIVE_PORT, debug=True)
