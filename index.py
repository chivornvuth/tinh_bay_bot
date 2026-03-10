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
    # Render/Replit usually provide a PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. Bot Setup ---
# Ensure these environment variables are set in your hosting provider (Replit/Render/Heroku)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

# --- DEBUG: CHECK IF KEY EXISTS ---
if not GEMINI_KEY:
    print("[ERROR] GEMINI_KEY is MISSING from environment variables!")
else:
    # Print only the first and last 3 characters for security
    print(f"[DEBUG] GEMINI_KEY found: {GEMINI_KEY[:3]}...{GEMINI_KEY[-3:]}")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

# Use the 1.5-flash model for faster, cheaper processing
model = ai.GenerativeModel('gemini-2.5-flash')  # Current stable workhorse

# This list stores orders in memory (will reset if bot restarts)
daily_orders = []

@bot.message_handler(func=lambda m: True if m.text and ("បាយ" in m.text or any(c.isdigit() for c in m.text)) else False)
def collect_orders(message):
    order_info = f"{message.from_user.first_name}: {message.text}"
    daily_orders.append(order_info)
    print(f"[LOG] Saved order: {order_info}")

@bot.message_handler(commands=['sum'])
def summarize_saved_orders(message):
    print(f"[LOG] Summarizing {len(daily_orders)} orders...")
    
    if not daily_orders:
        bot.reply_to(message, "មិនទាន់មានការកម្ម៉ង់នៅឡើយទេ! (No orders saved yet!)")
        return

    raw_text = "\n".join(daily_orders)
    
    # Refined prompt for better Khmer processing
    prompt = (
        f"You are a canteen assistant. Extract lunch orders from this list: \n{raw_text}\n"
        "Create a Markdown table with columns: 'Name', 'Dish', 'Quantity'. "
        "At the bottom, provide a 'Grand Total' of all items. Respond in Khmer if possible."
    )
    
    try:
        response = model.generate_content(prompt)
        
        # Checking if the AI actually returned content
        if response.text:
            bot.reply_to(message, response.text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "AI returned an empty response. Check logs.")
            
    except Exception as e:
        # This prints the EXACT error to your terminal/hosting log
        error_msg = str(e)
        print(f"[ERROR] Gemini API Failure: {error_msg}")
        
        if "API_KEY_INVALID" in error_msg:
            bot.reply_to(message, "កំហុស៖ API Key របស់អ្នកមិនត្រឹមត្រូវទេ។ (Invalid API Key)")
        elif "quota" in error_msg.lower():
            bot.reply_to(message, "កំហុស៖ អស់ quota ប្រើប្រាស់ហើយ។ (Quota Exceeded)")
        else:
            bot.reply_to(message, f"AI Error: {error_msg[:100]}...")

@bot.message_handler(commands=['clear'])
def clear_orders(message):
    global daily_orders
    daily_orders = []
    bot.reply_to(message, "បញ្ជីត្រូវបានលុប! (Order list has been cleared!)")

if __name__ == "__main__":
    # Start Web Server
    server_thread = Thread(target=run_web)
    server_thread.start()
    
    print("[DEBUG] Bot is starting polling...")
    bot.infinity_polling()
