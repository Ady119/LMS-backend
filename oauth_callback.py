# oauth_callback.py
from flask import Flask, request

app = Flask(__name__)

@app.route('/oauth/callback')
def oauth_callback():
    code = request.args.get("code")
    return f"<h2>Your AUTH_CODE is:</h2><code>{code}</code><p>Copy it and paste it into your script.</p>"

if __name__ == "__main__":
    app.run(port=5000)
