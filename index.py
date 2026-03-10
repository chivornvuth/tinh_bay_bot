### Complete Python Script
import os, telebot
from flask import Flask
from threading import Thread
import google.generativeai as ai

# --- 1. Keep-Alive Web Server (For Render/Replit) ---
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

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    print("[ERROR] Missing Environment Variables! Check your Secrets/Config.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

# Using the 2026 stable model to avoid 404 errors
MODEL_NAME = 'gemini-2.5-flash'
model = ai.GenerativeModel(MODEL_NAME)

# In-memory storage for orders
daily_orders = []

# --- 3. Message Handlers ---

# Collects messages containing "បាយ" or numbers
@bot.message_handler(func=lambda m: m.text and ("បាយ" in m.text or any(c.isdigit() for c in m.text)))
def collect_orders(message):
    order_info = f"{message.from_user.first_name}: {message.text}"
    daily_orders.append(order_info)
    print(f"[LOG] Saved order: {order_info}")

# Summarize orders using AI
@bot.message_handler(commands=['sum'])
def summarize_saved_orders(message):
    print(f"[LOG] Generating summary for {len(daily_orders)} orders...")
    
    if not daily_orders:
        bot.reply_to(message, "មិនទាន់មានការកម្ម៉ង់នៅឡើយទេ! (No orders saved yet!)")
        return

    raw_text = "\n".join(daily_orders)
    
    # Strictly instruct the AI to use triple backticks to avoid Telegram Parse Errors
    prompt = (
        f"Summarize these Khmer lunch orders: \n{raw_text}\n\n"
        "Create a clean table with 'Name', 'Dish', and 'Quantity'. "
        "Calculate total rice (បាយ) at the bottom. "
        "IMPORTANT: Wrap your entire response inside triple backticks like this: ``` [table] ```"
    )
    
    try:
        response = model.generate_content(prompt)
        
        if response.text:
            # We use Markdown mode. The triple backticks from the prompt 
            # will ensure Telegram treats it as a 'preformatted' block.
            bot.reply_to(message, response.text, parse_mode="Markdown")
        else:
            bot.reply_to(message, "AI returned no text. Try again.")
            
    except Exception as e:
        error_str = str(e)
        print(f"[ERROR] {error_str}")
        
        # Friendly error messages for common issues
        if "404" in error_str:
            bot.reply_to(message, "Error: Model not found. Please update the model name in the code.")
        elif "400" in error_str:
            bot.reply_to(message, "Error: Telegram couldn't read the AI's formatting. Try /sum again.")
        else:
            bot.reply_to(message, f"AI Error: {error_str[:50]}...")

# Clear the list
@bot.message_handler(commands=['clear'])
def clear_orders(message):
    global daily_orders
    daily_orders = []
    bot.reply_to(message, "បញ្ជីត្រូវបានលុប! (Order list has been cleared!)")

# --- 4. Execution ---
if __name__ == "__main__":
    # Start web server thread
    Thread(target=run_web).start()
    
    print(f"[DEBUG] Bot is running with model {MODEL_NAME}...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"[CRITICAL] Bot stopped: {e}")
