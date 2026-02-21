"""
A front end flask service to run the calorie counter application.
Retrieves cookie from backend as a JWT to authenticate user. 

Some notes about how things are being used:
1. Flask creates the application, render_template relies in jinja2 for dynamic output 
from static files. 
2. Proving authentication: Using jwt.
Way 1: Used on this app. Uses JWT_PUBLIC_KEY and JWT_PRIVATE_KEY to verify user. 
Way 2: Not used on this app. Uses JWT_SHARED_SECRET to verify user. Should only be used between backend servers. 
"""

from flask import Flask, redirect, request, url_for, render_template, make_response
import jwt

BACKEND_URL = 'http://localhost:7001/'
app = Flask(__name__)

# ---------------------
# Routes
# ---------------------
@app.route("/")
def welcome():
    return render_template("index.html")

@app.route("/login")
def login():
    # Http 302 code response and URL
    return redirect(f"{BACKEND_URL}/login?app=Flask")
    
@app.route("/calorie-counter/home")
def calorie_counter_home():
    """
    Validates private/public JWT tokens and then moves user to homepage
    """
    token = request.cookies.get("jwt_calorie_counter_profile")

    if not token:
        print("Cookie not found")
        return redirect(url_for("login"))

    with open("public.pem", "rb") as f:
        # Raw bites used in crypto encoding
        public_key = f.read()
    try:
        user_info = jwt.decode(token, public_key, algorithms=["RS256"]) # "R" for decoding private/public
    except jwt.ExpiredSignatureError:
        print("JWT expired")
        return redirect(url_for("login"))
    except jwt.InvalidTokenError:
        print("Invalid JWT.")
        return redirect(url_for("login"))

    return render_template("calorie-counter/home.html", user=user_info)

@app.route("/logout")
def logout():
    """
    Invalidates the JWT cookie
    """
    response = make_response(render_template("index.html"))
    response.set_cookie("jwt_calorie_counter_profile", "", expires=0, httponly=True, secure=False)  # set secure=True in production
    return response

if __name__ == "__main__":
    app.run(port=8000, debug=True)
