from flask import Flask, request, jsonify
import threading, time, requests, os, json
from datetime import datetime
from byte import Encrypt_ID, encrypt_api

app = Flask(__name__)
users_file = "users.json"
TOKEN = None
TOKEN_EXPIRY = 0

def get_author_info():
    return "API BY : XZANJA"

def save_user(uid):
    users = {}
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    now = int(time.time())
    expiry = now + 86400
    users[uid] = {
        "added_at": now,
        "expires_at": expiry
    }
    with open(users_file, "w") as f:
        json.dump(users, f)

def clean_expired_uids():
    if not os.path.exists(users_file):
        return {}
    with open(users_file, "r") as f:
        users = json.load(f)
    now = int(time.time())
    users = {uid: data for uid, data in users.items() if data["expires_at"] > now}
    with open(users_file, "w") as f:
        json.dump(users, f)
    return users

def fetch_token():
    global TOKEN_EXPIRY
    url = "https://tokan-plum.vercel.app/GeneRate-Jwt?Uid=3990840341&Pw=22268B73D724B70948A7263FF3D7C375C7908A72BDA4C3BB23E2E9FFA7F9E6FC"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            token = response.text.strip()
            if token:
                TOKEN_EXPIRY = time.time() + (5 * 60 * 60)
                return token
    except Exception as e:
        print("⚠️ Error fetching token:", e)
    return None

def update_token():
    global TOKEN
    while True:
        TOKEN = fetch_token()
        time.sleep(5 * 60 * 60)

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
        return "🚫 Token not available yet. Please try later."
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
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "close",
        "Accept-Encoding": "gzip, deflate, br"
    }
    try:
        response = requests.post(url, headers=headers, data=bytes.fromhex(encrypted_payload))
        if response.status_code == 200:
            return True
        else:
            return f"⚠️ Request failed: {response.status_code}\\n📩 {response.text}"
    except Exception as e:
        return f"🚫 Error sending request: {str(e)}"

@app.route("/send_friend", methods=["GET", "POST"])
def send_friend():
    if request.method == "GET":
        uid = request.args.get("uid")
    else:
        data = request.json
        uid = data.get("uid") if data else None

    if not uid:
        return jsonify({"error": "UID is required.", "developer": get_author_info()}), 400

    result = send_friend_request(uid)
    if result is not True:
        return jsonify({"result": result, "developer": get_author_info()}), 400

    save_user(uid)
    now = int(time.time())
    expires = now + 86400

    return jsonify({
        "status": "✅ Friend request sent successfully.",
        "UID": uid,
        "added_at": datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S"),
        "remaining_time": format_remaining_time(expires),
        "expires_at": datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S"),
        "duration": "1 day only",
        "developer": get_author_info()
    })

@app.route("/")
def index():
    users = clean_expired_uids()
    return jsonify({
        "total_users": len(users),
        "users": list(users.keys()),
        "token_expires_in": format_remaining_time(TOKEN_EXPIRY),
        "developer": get_author_info()
    })

if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))