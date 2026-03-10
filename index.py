import os, telebot
from flask import Flask
from threading import Thread
import google.generativeai as ai

# --- 1. Keep-Alive Web Server ---
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Active!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. Bot Setup & Validation ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# ADMIN_ID can now be a single ID or a list separated by commas
# Example in Environment Variables: ADMIN_ID = 123456,987654
raw_admin_ids = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [admin.strip() for admin in raw_admin_ids.split(",") if admin.strip()]

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    print("[ERROR] Missing Environment Variables!")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

MODEL_NAME = 'gemini-2.5-flash-preview-09-2025'
model = ai.GenerativeModel(MODEL_NAME)

# In-memory storage for orders
daily_orders = []

# --- Helper: Security Check ---
def is_admin(user_id):
    if not ADMIN_IDS:
        # If no ADMIN_ID is set, allow everyone (safety fallback)
        return True
    return str(user_id) in ADMIN_IDS

# --- 3. Message Handlers ---

# Everyone can order
@bot.message_handler(func=lambda m: m.text and ("បាយ" in m.text or any(c.isdigit() for c in m.text)))
def collect_orders(message):
    order_info = f"{message.from_user.first_name}: {message.text}"
    daily_orders.append(order_info)
    print(f"[LOG] Saved order: {order_info}")

# Only Admin list can sum
@bot.message_handler(commands=['sum'])
def summarize_saved_orders(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ កំហុស៖ អ្នកមិនមែនជា Admin ទេ ដូច្នេះអ្នកមិនអាចប្រើបញ្ជានេះបានឡើយ។ (Error: You are not an admin.)")
        return

    if not daily_orders:
        bot.reply_to(message, "មិនទាន់មានការកម្ម៉ង់នៅឡើយទេ!")
        return

    raw_text = "\n".join(daily_orders)
    
    prompt = (
        f"Extract and summarize these Khmer lunch orders: \n{raw_text}\n\n"
        "Instructions:\n"
        "1. Only show the dish name and total quantity (e.g., ស្ងោរជីឆាយ x3).\n"
        "2. Do not include person names.\n"
        "3. At the end, show the total rice count (បាយ x6).\n"
        "4. Use very simple plain text.\n"
        "5. Respond only with the list of items and totals."
    )
    
    try:
        response = model.generate_content(prompt)
        if response.text:
            bot.send_message(message.chat.id, response.text)
        else:
            bot.reply_to(message, "AI error.")
    except Exception as e:
        print(f"[ERROR] {e}")
        bot.reply_to(message, "កំហុសក្នុងការសង្ខេបបញ្ជី។")

# Only Admin list can clear
@bot.message_handler(commands=['clear'])
def clear_orders(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ កំហុស៖ អ្នកមិនមែនជា Admin ទេ ដូច្នេះអ្នកមិនអាចលុបបញ្ជីនេះបានឡើយ។ (Error: You are not an admin.)")
        return
        
    global daily_orders
    daily_orders = []
    bot.reply_to(message, "បញ្ជីត្រូវបានលុប!")

if __name__ == "__main__":
    Thread(target=run_web).start()
    print(f"[DEBUG] Bot is running with {MODEL_NAME}...")
    bot.infinity_polling()
