import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

@app.route("/", methods=["GET"])
def home():
    return "Facebook Messenger Chatbot is running! 🤖"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            print("❌ Webhook verification failed!")
            return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        print("🔔 Received webhook data:", data)

        if "entry" in data:
            for entry in data["entry"]:
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    if "message" in messaging_event and "text" in messaging_event["message"]:
                        user_message = messaging_event["message"]["text"]
                        print(f"👤 User message: {user_message}")
                        bot_reply = get_openrouter_response(user_message)
                        send_message(sender_id, bot_reply)

        return "EVENT_RECEIVED", 200

def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            print("📨 Message sent successfully!")
        else:
            print(f"❌ Failed to send message: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")

def get_openrouter_response(message):
    try:
        if not OPENROUTER_API_KEY:
            print("❌ OpenRouter API key not found")
            return "حدث خطأ: مفتاح API غير متوفر"
        
        if not MODEL_ID:
            print("❌ Model ID not found")
            return "حدث خطأ: معرف النموذج غير متوفر"

        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": "أنت مساعد ذكي يتكلم بالعربية ويساعد المستخدمين بطريقة مفيدة ومهذبة."},
                {"role": "user", "content": message}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        print(f"🔄 Calling OpenRouter with model: {MODEL_ID}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received successfully")
            
            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"]
                print(f"🤖 Bot reply: {reply}")
                return reply
            else:
                print("❌ No choices in response")
                return "عذراً، لم أتمكن من الحصول على رد مناسب"
        else:
            print(f"❌ OpenRouter API Error: {response.status_code}")
            print(f"❌ Error response: {response.text}")
            return f"حدث خطأ أثناء الاتصال: {response.status_code}"

    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return "حدث خطأ: انتهت مهلة الطلب"
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {str(e)}")
        return "حدث خطأ في الشبكة"
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return "حدث خطأ غير متوقع"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)