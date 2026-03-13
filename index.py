import os, telebot
from flask import Flask
from threading import Thread
import google.generativeai as ai
from datetime import datetime # Added for date filtering

# --- 1. Keep-Alive Web Server ---
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. Bot Setup ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

raw_admin_ids = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [admin.strip() for admin in raw_admin_ids.split(",") if admin.strip()]

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

# កែប្រែត្រឡប់ទៅប្រើ gemini-2.5-flash វិញតាមការស្នើសុំ
MODEL_NAME = 'gemini-2.5-flash'
model = ai.GenerativeModel(MODEL_NAME)

# In-memory storage: Now stores dictionaries with timestamps
# Structure: {"user": "Name", "text": "Order text", "date": datetime.date}
daily_orders = []

# --- Helpers ---
def is_admin(user_id):
    if not ADMIN_IDS:
        return True
    return str(user_id) in ADMIN_IDS

def get_today_orders():
    """Returns only orders placed today."""
    today = datetime.now().date()
    return [order['text'] for order in daily_orders if order['date'] == today]

# --- 3. Message Handlers ---

@bot.message_handler(func=lambda m: m.text and ("បាយ" in m.text or any(c.isdigit() for c in m.text)))
def collect_orders(message):
    # Store order with the current date
    order_data = {
        "user": message.from_user.first_name,
        "text": message.text,
        "date": datetime.now().date()
    }
    daily_orders.append(order_data)
    print(f"[LOG] Saved order for {order_data['date']}: {message.text}")

@bot.message_handler(commands=['sum'])
def summarize_saved_orders(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ អ្នកមិនមែនជា Admin ទេ។")
        return

    # Filter to get only today's list
    todays_list = get_today_orders()

    if not todays_list:
        bot.reply_to(message, "មិនទាន់មានការកម្ម៉ង់សម្រាប់ថ្ងៃនេះនៅឡើយទេ!")
        return

    raw_text = "\n".join(todays_list)
    
    prompt = (
        f"Extract and summarize these Khmer lunch orders for today: \n{raw_text}\n\n"
        "Instructions:\n"
        "1. Group identical dishes and sum their quantities.\n"
        "2. Format: [Dish Name] x[Total Quantity] (e.g., ឆាសាច់ជ្រូក x3).\n"
        "3. Do not include names of people.\n"
        "4. Calculate the total count of 'Rice' (បាយ) separately at the bottom (e.g., សរុបបាយ x10).\n"
        "5. Respond only with the summarized list in plain text."
    )
    
    try:
        response = model.generate_content(prompt)
        if response.text:
            bot.send_message(message.chat.id, f"📋 **បញ្ជីកម្ម៉ង់អាហារថ្ងៃនេះ ({datetime.now().strftime('%d/%m/%Y')}):**\n\n{response.text}")
        else:
            bot.reply_to(message, "AI error.")
    except Exception as e:
        print(f"[ERROR] {e}")
        bot.reply_to(message, "កំហុសក្នុងការសង្ខេបបញ្ជី។")

@bot.message_handler(commands=['clear'])
def clear_orders(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ អ្នកមិនមែនជា Admin ទេ។")
        return
        
    global daily_orders
    daily_orders = [] # This clears everything (all dates)
    bot.reply_to(message, "បញ្ជីទាំងអស់ត្រូវបានលុបចេញពី Memory!")

if __name__ == "__main__":
    Thread(target=run_web).start()
    print(f"[DEBUG] Bot is running with {MODEL_NAME}...")
    bot.infinity_polling()
