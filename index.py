import os
import telebot
from flask import Flask
from threading import Thread
from datetime import datetime
import google.generativeai as ai

# --- 1. Keep-Alive Web Server for Render ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    print("[DEBUG] Flask server starting on port 10000...")
    app.run(host='0.0.0.0', port=10000)

# --- 2. Bot Configuration ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

@bot.message_handler(commands=['sum'])
def summarize_daily(message):
    print(f"\n[LOG] Received /sum command from {message.from_user.first_name} (@{message.from_user.username})")
    
    chat_id = message.chat.id
    today = datetime.now().date()
    daily_text = ""

    try:
        print(f"[LOG] Attempting to fetch chat history for Chat ID: {chat_id}")
        # Fetch last 100 messages
        history = bot.get_chat_history(chat_id, limit=100)
        print(f"[LOG] Successfully retrieved {len(history)} messages from history.")
        
        for msg in history:
            msg_date = datetime.fromtimestamp(msg.date).date()
            if msg_date == today and msg.text:
                # Log every message the bot "sees" to check if it's blind
                print(f"  > Analyzing message: {msg.text[:30]}...")
                
                # Check for keywords like 'បាយ' or numbers
                if "បាយ" in msg.text or any(char.isdigit() for char in msg.text):
                    daily_text += f"\n{msg.from_user.first_name}: {msg.text}"

        if not daily_text:
            print("[LOG] No orders matched for today's date.")
            bot.reply_to(message, "រកមិនឃើញការកម្ម៉ង់សម្រាប់ថ្ងៃនេះទេ! (No orders found for today!)")
            return

        print(f"[LOG] Sending gathered data to Gemini AI...")
        model = ai.GenerativeModel('gemini-1.5-pro')
        prompt = f"Extract and sum all food orders from this text for today. Format as a clean Khmer table with 'Dish' and 'Quantity'. Calculate the 'Total Rice (សរុបបាយ)' at the bottom. Data: {daily_text}"
        
        response = model.generate_content(prompt)
        print("[LOG] AI response received. Sending to Telegram group.")
        bot.reply_to(message, response.text)

    except Exception as e:
        print(f"[ERROR] Logic Failure: {e}")
        bot.reply_to(message, "Error: Make sure the bot is an ADMIN to read chat history.")

# --- 3. Start Both Services ---
if __name__ == "__main__":
    # Start web server thread
    t = Thread(target=run_web)
    t.daemon = True # Allows thread to exit when main program exits
    t.start()
    
    print("[DEBUG] Telegram bot is initiating polling...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"[CRITICAL] Bot Polling Failed: {e}")
