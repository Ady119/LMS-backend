import requests
from urllib.parse import urlencode

# Replace these with your actual values
APP_KEY = "j6zbrgkqj7ord9t"
APP_SECRET = "efmzxfaph03cxz9"
AUTH_CODE = "m-Zzy48ZEPIAAAAAAAAAUIcvtrRnHi8j3f8l8bQR82I"
REDIRECT_URI = "http://localhost:5000/oauth/callback"

response = requests.post(
    "https://api.dropboxapi.com/oauth2/token",
    data=urlencode({
        "code": AUTH_CODE,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }),
    auth=(APP_KEY, APP_SECRET),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

print(response.json())

