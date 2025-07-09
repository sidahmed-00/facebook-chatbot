from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'sido009')
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# OpenRouter configuration
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1-0528:free"

@app.route('/', methods=['GET'])
def verify():
    """Verify webhook endpoint"""
    return "Facebook Chatbot is running!"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify webhook with Facebook"""
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return challenge
    else:
        print("❌ Webhook verification failed!")
        return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages from Facebook"""
    try:
        data = request.get_json()
        print(f"🔔 Received webhook data: {data}")
        
        if data['object'] == 'page':
            for entry in data['entry']:
                for messaging_event in entry.get('messaging', []):
                    if 'message' in messaging_event:
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message'].get('text', '')
                        
                        print(f"👤 User message: {message_text}")
                        
                        # Generate AI response
                        ai_response = get_ai_response(message_text)
                        
                        # Send response back to user
                        send_message(sender_id, ai_response)
        
        return "OK", 200
    
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return "Error", 500

def get_ai_response(user_message):
    """Get AI response from OpenRouter using DeepSeek model"""
    try:
        print(f"🔄 Calling OpenRouter with model: {MODEL_NAME}")
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://facebook-chatbot-n2sf.onrender.com",
            "X-Title": "Facebook Chatbot"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful and friendly AI assistant. Keep your responses concise and conversational, suitable for a Facebook Messenger chat."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔍 Full API response: {result}")
            
            # Check if response has the expected structure
            if 'choices' in result and len(result['choices']) > 0:
                ai_message = result['choices'][0]['message']['content'].strip()
                print(f"🤖 AI response: '{ai_message}'")
                
                # Check if AI response is empty
                if not ai_message or ai_message.strip() == "":
                    print("⚠️ Empty AI response, using fallback")
                    return "I'm here to help! Could you please rephrase your question?"
                
                return ai_message
            else:
                print("❌ Invalid API response structure")
                return "Sorry, I received an invalid response. Please try again."
        else:
            print(f"❌ OpenRouter API Error: {response.status_code}")
            print(f"❌ Error response: {response.text}")
            return "Sorry, I'm having trouble processing your message right now. Please try again later."
    
    except requests.exceptions.Timeout:
        print("❌ OpenRouter API timeout")
        return "Sorry, I'm taking too long to respond. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenRouter API request error: {str(e)}")
        return "Sorry, I'm having technical difficulties. Please try again later."
    except Exception as e:
        print(f"❌ Unexpected error in get_ai_response: {str(e)}")
        return "Sorry, something went wrong. Please try again."

def send_message(recipient_id, message_text):
    """Send message to Facebook user"""
    try:
        # Validate message text
        if not message_text or message_text.strip() == "":
            message_text = "Sorry, I couldn't generate a response. Please try again."
            print("⚠️ Empty message detected, using fallback response")
        
        # Ensure message is not too long (Facebook limit is 2000 characters)
        if len(message_text) > 2000:
            message_text = message_text[:1997] + "..."
            print("⚠️ Message truncated due to length limit")
        
        print(f"📤 Sending message: {message_text}")
        
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("📨 Message sent successfully!")
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"❌ Error response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")

if __name__ == '__main__':
    # Check if required environment variables are set
    if not PAGE_ACCESS_TOKEN:
        print("❌ Warning: PAGE_ACCESS_TOKEN not found in environment variables")
    if not OPENROUTER_API_KEY:
        print("❌ Warning: OPENROUTER_API_KEY not found in environment variables")
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
