import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
AUTH_CODE = os.getenv("DROPBOX_AUTH_CODE")
REDIRECT_URI = os.getenv("DROPBOX_REDIRECT_URI")

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
