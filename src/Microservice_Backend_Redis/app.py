from flask import Flask, jsonify, request
from cryptography.hazmat.primitives import serialization
import jwt

# -----------------------------
# A backend microservice to update the Redis database.
# It also verifies the JWT token before retrieving information. 
# -----------------------------
PORT = 7002
DEBUG_MODE = True

app = Flask(__name__)

# -----------------------------
# Routes
# -----------------------------
@app.route("/add_JWT_token")
def add_JWT_token():
    pass

@app.route("/update_JWT_token")
def verify_JWT_token():
    """
    Verifies JWT token expiration, sends error if not
    Invalidates old device if new device is signed in
    Adds to Redis database as refreshed, sends error if session expired
    """
    # Veririfies JWT token is valid and not expired
    verify_jwt_status = verify_user()
    verify_jwt_dict = verify_jwt_status.get_json()
    if not verify_jwt_dict.get("success"):
        return verify_jwt_dict
    
    # TODO: Invalidates old device if new device is signed in

    # TODO: Adds to Redis database as refreshed, sends error if session expired
    return verify_jwt_dict # Change later
    
@app.route("/remove_JWT_token")
def remove_JWT_token():
    """
    Removes JWT token if 
    """
    pass

# -----------------------------
# HELPERS
# -----------------------------
def verify_user():
    """
    Verifies the user's JWT and expiration
    """
    token = request.headers.get("Authorization", None)
    print(token)
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

# Initialize application
if __name__ == "__main__":
    app.run(port=PORT, debug=DEBUG_MODE)