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
import requests

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
    return redirect(f"{BACKEND_URL}/login?app-type=Flask")
    
@app.route("/calorie-counter/home")
def calorie_counter_home():
    """
    Validates private/public JWT tokens and then moves user to homepage
    """
    token = request.cookies.get("jwt_calorie_counter_profile")

    if not token:
        print("Cookie not found")
        return redirect(url_for("login"))

    # TODO Send request to backend/verify-user and decide to redirect based on the response.
    # user_info can be in the response if it's successful.
    headers = {"Authorization": token}
    resp = requests.get(f"{BACKEND_URL}/verify-user", headers=headers)
    if not resp.json().get("success"):
        print("User verification failed.")
        return redirect(url_for("logout"))

    return render_template("calorie-counter/home.html", user=resp.json().get("user_info"))

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