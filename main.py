from flask import Flask, request, jsonify
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
    url = "https://aditya-jwt-v11op.onrender.com/token?uid=3831627617&password=CAC2F2F3E2F28C5F5944D502CD171A8AAF84361CDC483E94955D6981F1CFF3E3"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            token = response.text.strip()
            if token:
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
            return f"⚠️ Request failed: {response.status_code}\n📩 {response.text}"
    except Exception as e:
        return f"🚫 Error sending request: {str(e)}"

def get_game_info(player_id):
    if not TOKEN:
        return None, "Token not available"
    
    encrypted_id = Encrypt_ID(player_id)
    payload = f"08a7c4839f1e10{encrypted_id}1801"
    encrypted_payload = encrypt_api(payload)
    
    url = "https://clientbp.ggblueshark.com/GetPlayerInfo"
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
            return response.json(), None
        else:
            return None, f"Request failed with status {response.status_code}"
    except Exception as e:
        return None, f"Error getting player info: {str(e)}"

@app.route("/send_friend", methods=["GET", "POST"])
def send_friend():
    try:
        uid = None
        nickname = None
        
        if request.method == "GET":
            uid = request.args.get("uid")
            nickname = request.args.get("nickname")
        else:
            data = request.json
            uid = data.get("uid") if data else None
            nickname = data.get("nickname") if data else None

        if not uid:
            return jsonify({"error": "UID is required.", "developer": get_author_info()}), 400

        # جلب معلومات اللاعب من API إذا لم يتم تقديم الاسم
        if not nickname:
            player_info, error = get_game_info(uid)
            if player_info and "nickname" in player_info:
                nickname = player_info["nickname"]
            else:
                nickname = "Unknown"

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

@app.route("/player_info", methods=["GET"])
def player_info():
    try:
        uid = request.args.get("uid")
        if not uid:
            return jsonify({"error": "UID is required.", "developer": get_author_info()}), 400
        
        info, error = get_game_info(uid)
        if error:
            return jsonify({"error": error, "developer": get_author_info()}), 400
        
        nickname = info.get("nickname") if info else None
        
        users = {}
        if os.path.exists(users_file):
            with open(users_file, "r") as f:
                users = json.load(f)
        
        is_added = uid in users
        added_info = None
        if is_added:
            saved_nickname = users[uid].get("nickname", nickname)
            added_info = {
                "nickname": saved_nickname,
                "added_at": datetime.fromtimestamp(users[uid]["added_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "expires_at": datetime.fromtimestamp(users[uid]["expires_at"]).strftime("%Y-%m-%d %H:%M:%S"),
                "remaining_time": format_remaining_time(users[uid]["expires_at"])
            }
        
        return jsonify({
            "player_info": info,
            "is_added": is_added,
            "added_info": added_info,
            "developer": get_author_info()
        })
        
    except Exception as e:
        app.logger.error("❌ Error in /player_info: %s", e, exc_info=True)
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/")
def index():
    users = clean_expired_uids()
    users_list = []
    for uid, data in users.items():
        users_list.append({
            "uid": uid,
            "nickname": data.get("nickname", "Unknown"),
            "added_at": datetime.fromtimestamp(data["added_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": datetime.fromtimestamp(data["expires_at"]).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return jsonify({
        "total_users": len(users),
        "users": users_list,
        "token_expires_in": format_remaining_time(TOKEN_EXPIRY),
        "developer": get_author_info()
    })

if __name__ == "__main__":
    TOKEN = fetch_token()
    threading.Thread(target=update_token, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))