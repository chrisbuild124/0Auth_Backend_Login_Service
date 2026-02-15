import requests

PORT=5005
DOMAIN=f'http://localhost:{PORT}/auth'
APP_TYPE='CLI'

# Domain 'app-type': app-type
# 'Web', 'CLI'

result = requests.post(
    DOMAIN,
    json={'app-type': 'CLI'}
)

login_url = result.json()
print(login_url) # Should be the login URL to authenticate

# Need a way to get back the auth0 userID