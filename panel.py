import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import re
from datetime import datetime, timedelta
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Disable SSL Warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
JSON_FILE_PATH = './Allowed_user.json'

# Encrypt Functions
def Encrypt(number):
    number = int(number)
    encoded_bytes = []
    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80
        encoded_bytes.append(byte)
        if not number:
            break
    return bytes(encoded_bytes).hex()

def encrypt_api(plain_text):
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

# Token Management Functions
def guest_token(uid, password):
    url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    headers = {
        "Host": "100067.connect.garena.com", 
        "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)", 
        "Content-Type": "application/x-www-form-urlencoded", 
        "Accept-Encoding": "gzip, deflate, br", 
        "Connection": "close"
    }
    data = {
        "uid": f"{uid}", 
        "password": f"{password}", 
        "response_type": "token", 
        "client_type": "2", 
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3", 
        "client_id": "100067"
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        data = response.json()
        NEW_ACCESS_TOKEN = data['access_token']
        NEW_OPEN_ID = data['open_id']
        return TOKEN_MAKER(NEW_ACCESS_TOKEN, NEW_OPEN_ID)
    except Exception as e:
        print(f"Error getting guest token: {e}")
        return None

def TOKEN_MAKER(NEW_ACCESS_TOKEN, NEW_OPEN_ID):
    PAYLOAD = b':\x071.108.3\xaa\x01\x02ar\xb2\x01 55ed759fcf94f85813e57b2ec8492f5c\xba\x01\x014\xea\x01@6fb7fdef8658fd03174ed551e82b71b21db8187fa0612c8eaf1b63aa687f1eae\x9a\x06\x014\xa2\x06\x014\xca\x03 7428b253defc164018c604a1ebbfebdf'
    PAYLOAD = PAYLOAD.replace(b"6fb7fdef8658fd03174ed551e82b71b21db8187fa0612c8eaf1b63aa687f1eae", NEW_ACCESS_TOKEN.encode("UTF-8"))
    PAYLOAD = PAYLOAD.replace(b"55ed759fcf94f85813e57b2ec8492f5c", NEW_OPEN_ID.encode("UTF-8"))
    PAYLOAD = PAYLOAD.hex()
    PAYLOAD = encrypt_api(PAYLOAD)
    PAYLOAD = bytes.fromhex(PAYLOAD)
    URL = "https://loginbp.common.ggbluefox.com/MajorLogin"
    headers = {
        "Expect": "100-continue", 
        "Authorization": "Bearer", 
        "X-Unity-Version": "2018.4.11f1", 
        "X-GA": "v1 1", 
        "ReleaseVersion": "OB47", 
        "Content-Type": "application/x-www-form-urlencoded", 
        "Content-Length": str(len(PAYLOAD.hex())), 
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)", 
        "Host": "loginbp.common.ggbluefox.com", 
        "Connection": "close", 
        "Accept-Encoding": "gzip, deflate, br"
    }
    try:
        RESPONSE = requests.post(URL, headers=headers, data=PAYLOAD, verify=False)
        if RESPONSE.status_code == 200:
            if len(RESPONSE.text) < 10:
                return False
            BASE64_TOKEN = RESPONSE.text[RESPONSE.text.find("eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ"):-1]
            second_dot_index = BASE64_TOKEN.find(".", BASE64_TOKEN.find(".") + 1)
            BASE64_TOKEN = BASE64_TOKEN[:second_dot_index+44]
            return BASE64_TOKEN
    except Exception as e:
        print(f"Error during TOKEN_MAKER: {e}")
        return None

def GetToken():
    return guest_token("3732763933", "E541471C63AA7C8345E0570FBBB68040EA4D40F270AD86D7B2C4E8DF0C438FAF")

# Request Handler
def sendrequest(target_id, token):
    url = "https://clientbp.common.ggbluefox.com/RequestAddingFriend"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded", 
        "X-GA": "v1 1", 
        "ReleaseVersion": "OB47", 
        "Host": "clientbp.common.ggbluefox.com", 
        "Accept-Encoding": "gzip, deflate, br", 
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8", 
        "User-Agent": "Free%20Fire/2019117863 CFNetwork/1399 Darwin/22.1.0", 
        "Connection": "keep-alive", 
        "Authorization": f"Bearer {token}", 
        "X-Unity-Version": "2018.4.11f1", 
        "Accept": "/"
    }
    id_encrypted = Encrypt(target_id)
    data0 = "08c8b5cfea1810" + id_encrypted + "18012008"
    data = bytes.fromhex(encrypt_api(data0))
    try:
        response = requests.post(url, headers=headers, data=data, verify=False)
        print(response)
        return response
    except Exception as e:
        print(f"Error in sendrequest: {e}")
        return None

# Save User Data to JSON
def save_to_json(user_id, end_date):
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
    else:
        data = []

    if any(item['id'] == user_id for item in data):
        return False

    data.append({"id": user_id, "end_date": end_date})

    try:
        with open(JSON_FILE_PATH, 'w') as file:
            json.dump(data, file, indent=4)
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False

# تحويل الوقت المدخل إلى تاريخ مستقبلي
def calculate_end_date(time_str):
    match = re.match(r'^(1|15|30)(day|days)$', time_str)
    if match:
        days = int(match.group(1))
        today = datetime.today()
        future_date = today + timedelta(days=days)
        return future_date.strftime('%Y-%m-%d %H:%M:%S')
    return None

# وظيفة معالجة إضافة مستخدم
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2:
        await update.message.reply_text("Invalid command. Please use /add id time\nExample: /add 12345678 1day")
    else:
        user_id = context.args[0]
        time = context.args[1]

        if user_id.isdigit():
            end_date = calculate_end_date(time)
            if end_date:
                if save_to_json(user_id, end_date):
                    token = GetToken()
                    if token:
                        response = sendrequest(user_id, token)
                        if response and response.status_code == 200:
                            await update.message.reply_text(f"ID: {user_id} added with end date: {end_date}. Request sent successfully!")
                        else:
                            await update.message.reply_text(f"ID: {user_id} added with end date: {end_date}. But failed to send request.")
                    else:
                        await update.message.reply_text("Failed to generate token.")
                else:
                    await update.message.reply_text(f"ID: {user_id} already exists.\n")
            else:
                await update.message.reply_text("Please make sure the time is in the correct format: 1day, 15days, or 30day.\n")
        else:
            await update.message.reply_text("ID must be numeric.")

# وظيفة التشغيل الرئيسية للبوت
def main() -> None:
    app = ApplicationBuilder().token("7716626130:AAE5W2pcLQToHkKKbLEGeWHYSbafpuKlLdo").build()
    app.add_handler(CommandHandler("add", add))
    app.run_polling()

if __name__ == '__main__':
    main()  