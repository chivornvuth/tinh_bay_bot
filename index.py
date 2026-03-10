import os, telebot
from flask import Flask
from threading import Thread
import google.generativeai as ai

# --- 1. Keep-Alive Web Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Active!"

def run_web():
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 10000))

# --- 2. Bot Setup ---
bot = telebot.TeleBot(os.getenv("TELEGRAM_TOKEN"))
ai.configure(api_key=os.getenv("GEMINI_KEY"))

# --- DEBUG: CHECK IF KEY EXISTS ---
GEMINI_KEY = os.getenv("GEMINI_KEY")

if not GEMINI_KEY:
    print("[ERROR] GEMINI_KEY is MISSING from environment variables!")
else:
    # Print only the first and last 3 characters for security
    print(f"[DEBUG] GEMINI_KEY found: {GEMINI_KEY[:3]}...{GEMINI_KEY[-3:]}")

# This list will store orders sent while the bot is running
daily_orders = []

@bot.message_handler(func=lambda m: True if m.text and ("បាយ" in m.text or any(c.isdigit() for c in m.text)) else False)
def collect_orders(message):
    # This automatically "sees" and saves orders as they are sent
    order_info = f"{message.from_user.first_name}: {message.text}"
    daily_orders.append(order_info)
    print(f"[LOG] Saved order: {order_info}")

@bot.message_handler(commands=['sum'])
def summarize_saved_orders(message):
    print("[LOG] Received /sum command")
    
    if not daily_orders:
        bot.reply_to(message, "មិនទាន់មានការកម្ម៉ង់នៅឡើយទេ! (No orders saved yet!)")
        return

    # Join all saved orders into one text block
    raw_text = "\n".join(daily_orders)
    
    model = ai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Summarize these Khmer lunch orders into a clean table with 'Dish' and 'Quantity' columns. Calculate total rice (បាយ) at the bottom: {raw_text}"
    
    try:
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "AI Error. Please check your Gemini Key.")

@bot.message_handler(commands=['clear'])
def clear_orders(message):
    global daily_orders
    daily_orders = []
    bot.reply_to(message, "បញ្ជីត្រូវបានលុប! (Order list has been cleared!)")

if __name__ == "__main__":
    Thread(target=run_web).start()
    print("[DEBUG] Bot is running...")
    bot.infinity_polling()
