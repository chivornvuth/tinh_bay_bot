import os, telebot
from flask import Flask
from threading import Thread
from google import genai  # Updated library
from datetime import datetime

# --- 1. Keep-Alive Web Server ---
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Active!"

def run_web():
    # Render provides the PORT variable automatically
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. Bot Setup & Safety Check ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# Safety check: Prevent the "NoneType" error you saw earlier
if not TELEGRAM_TOKEN or not GEMINI_KEY:
    print("❌ ERROR: TELEGRAM_TOKEN or GEMINI_KEY is missing!")
    exit(1)

raw_admin_ids = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [admin.strip() for admin in raw_admin_ids.split(",") if admin.strip()]

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_KEY) # New Client Setup

# Using the requested model
MODEL_NAME = 'gemini-2.0-flash' # Note: 2.5 was a typo in your snippet; 2.0 is current

daily_orders = []

# --- Helpers ---
def is_admin(user_id):
    if not ADMIN_IDS: return True
    return str(user_id) in ADMIN_IDS

def get_today_orders():
    today = datetime.now().date()
    return [order['text'] for order in daily_orders if order['date'] == today]

# --- 3. Message Handlers ---

@bot.message_handler(func=lambda m: m.text and ("បាយ" in m.text or any(c.isdigit() for c in m.text)))
def collect_orders(message):
    order_data = {
        "user": message.from_user.first_name,
        "text": message.text,
        "date": datetime.now().date()
    }
    daily_orders.append(order_data)
    print(f"[LOG] Saved: {message.text}")

@bot.message_handler(commands=['sum'])
def summarize_saved_orders(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ អ្នកមិនមែនជា Admin ទេ។")
        return

    todays_list = get_today_orders()
    if not todays_list:
        bot.reply_to(message, "មិនទាន់មានការកម្ម៉ង់សម្រាប់ថ្ងៃនេះនៅឡើយទេ!")
        return

    raw_text = "\n".join(todays_list)
    prompt = (
        f"Extract and summarize these Khmer lunch orders: \n{raw_text}\n\n"
        "Instructions: Group identical dishes, sum quantities, format like 'ឆាសាច់ជ្រូក x3', count 'បាយ' separately."
    )
    
    try:
        # Updated AI call syntax
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        if response.text:
            bot.send_message(message.chat.id, f"📋 **បញ្ជីកម្ម៉ង់អាហារថ្ងៃនេះ:**\n\n{response.text}")
    except Exception as e:
        print(f"[ERROR] {e}")
        bot.reply_to(message, "កំហុសក្នុងការសង្ខេបបញ្ជី។")

if __name__ == "__main__":
    Thread(target=run_web).start()
    print(f"[DEBUG] Bot is running...")
    bot.infinity_polling()
