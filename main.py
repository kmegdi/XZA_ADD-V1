from flask import Flask, request, jsonify, Response
import threading, time, requests, os, json, logging
from datetime import datetime
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

users_file = "users.json"
TOKEN = None
TOKEN_EXPIRY = 0

def get_author_info():
    return "API BY : XZANJA"

def fetch_token():
    global TOKEN_EXPIRY
    url = "https://aditya-jwt-v11op.onrender.com/token?uid=3831627617&password=CAC2F2F3E2F28C5F5944D502CD171A8AAF84361CDC483E94955D6981F1CFF3E3"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            token = response.text.strip()
            if token.count('.') == 2:
                TOKEN_EXPIRY = time.time() + (5 * 60 * 60)
                return token
    except Exception as e:
        app.logger.error("Error fetching token: %s", e)
    return None

def update_token():
    global TOKEN
    while True:
        TOKEN = fetch_token()
        time.sleep(5 * 60 * 60)

def save_user(uid, nickname=None):
    users = {}
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    now = int(time.time())
    expiry = now + 86400
    users[uid] = {
        "added_at": now,
        "expires_at": expiry,
        "nickname": nickname
    }
    with open(users_file, "w") as f:
        json.dump(users, f)

def format_remaining_time(expiry_time):
    remaining = int(expiry_time - time.time())
    if remaining <= 0:
        return "⛔ Expired"
    days = remaining // 86400
    hours = (remaining % 86400) // 3600
    minutes = (remaining % 3600) // 60
    return f"{days} day(s) / {hours} hour(s) / {minutes} minute(s)"

def send_friend_request(player_id):
    if not TOKEN:
        return "🚫 Token not available. Try again later."
    encrypted_id = Encrypt_ID(player_id)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)
    url = "https://clientbp.ggblueshark.com/RequestAddingFriend"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": str(len(encrypted_payload)),
        "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }
    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            return True
        else:
            return f"⚠️ Request failed: {response.status_code}\n📩 {response.text}"
    except Exception as e:
        return f"🚫 Error sending request: {str(e)}"

@app.route("/send_friend", methods=["GET"])
def send_friend():
    try:
        uid = request.args.get("uid")
        nickname = request.args.get("nickname")
        if not uid:
            return jsonify({"error": "UID is required.", "developer": get_author_info()}), 400

        result = send_friend_request(uid)
        if result is not True:
            return jsonify({"result": result, "developer": get_author_info()}), 400

        save_user(uid, nickname)
        now = int(time.time())
        expires = now + 86400

        return jsonify({
            "status": "✅ Friend request sent successfully.",
            "UID": uid,
            "nickname": nickname,
            "added_at": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_time": format_remaining_time(expires),
            "expires_at": datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S"),
            "duration": "1 day only",
            "developer": get_author_info()
        })
    except Exception as e:
        app.logger.error("❌ Error in /send_friend: %s", e, exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/")
def home():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Free Fire Friend Request</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap');
    body {
      margin: 0;
      padding: 0;
      font-family: 'Orbitron', sans-serif;
      background: linear-gradient(to right, #0f0c29, #302b63, #24243e);
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      overflow: hidden;
    }
    .container {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 16px;
      padding: 30px 40px;
      box-shadow: 0 0 15px #00ffd5;
      text-align: center;
      animation: fadeIn 1.5s ease-in-out;
      backdrop-filter: blur(10px);
    }
    @keyframes fadeIn {
      0% { opacity: 0; transform: scale(0.95); }
      100% { opacity: 1; transform: scale(1); }
    }
    h1 {
      font-size: 24px;
      margin-bottom: 10px;
      color: #00ffd5;
    }
    p {
      font-size: 14px;
      margin-bottom: 25px;
      color: #ccc;
    }
    input[type="text"] {
      padding: 10px;
      width: 240px;
      border-radius: 6px;
      border: none;
      outline: none;
      font-size: 16px;
      text-align: center;
      margin-bottom: 20px;
    }
    button {
      padding: 10px 25px;
      background: #00ffd5;
      color: #000;
      font-weight: bold;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      transition: 0.3s ease;
    }
    button:hover {
      background: #00bfa6;
    }
    #response {
      margin-top: 20px;
      background-color: rgba(0, 0, 0, 0.3);
      padding: 12px;
      border-radius: 6px;
      font-size: 13px;
      color: #00ffcc;
      white-space: pre-wrap;
      max-height: 180px;
      overflow-y: auto;
    }
    .glow {
      color: #00ffd5;
      animation: glow 1.8s infinite alternate;
    }
    @keyframes glow {
      from {
        text-shadow: 0 0 5px #00ffd5, 0 0 10px #00ffd5, 0 0 20px #00ffd5;
      }
      to {
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff, 0 0 30px #00ffff;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <h1 class="glow">🔥 Welcome to Friend Request Sender 🔥</h1>
    <p>Enter your Free Fire UID below and send a real friend request!</p>
    <input type="text" id="uid" placeholder="Enter UID..." />
    <br>
    <button onclick="sendRequest()">Send Request</button>
    <div id="response"></div>
  </div>

  <script>
    async function sendRequest() {
      const uid = document.getElementById("uid").value;
      const responseBox = document.getElementById("response");
      if (!uid) {
        responseBox.textContent = "⚠️ Please enter a UID.";
        return;
      }
      responseBox.textContent = "⏳ Sending request...";
      try {
        const response = await fetch(`/send_friend?uid=${uid}`);
        const data = await response.json();
        responseBox.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        responseBox.textContent = "❌ Error sending request.";
      }
    }
  </script>
</body>
</html>
"""
    return Response(html_content, content_type='text/html')

if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))