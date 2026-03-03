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
    # Render uses port 10000 by default
    app.run(host='0.0.0.0', port=10000)

# --- 2. Bot Configuration ---
# Uses Environment Variables set in Render Dashboard
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

@bot.message_handler(commands=['sum'])
def summarize_daily_orders(message):
    chat_id = message.chat.id
    today = datetime.now().date()
    daily_text = ""

    try:
        # Fetch last 100 messages to find today's orders
        # Note: Bot must be an ADMIN to read history properly
        history = bot.get_chat_history(chat_id, limit=100)
        
        for msg in history:
            # Convert message timestamp to date
            msg_date = datetime.fromtimestamp(msg.date).date()
            
            # Only collect messages from today that look like orders
            if msg_date == today and msg.text:
                # Basic filter: check for Khmer rice (បាយ) or numbers
                if "បាយ" in msg.text or any(char.isdigit() for char in msg.text):
                    daily_text += f"\n{msg.from_user.first_name}: {msg.text}"

        if not daily_text:
            bot.reply_to(message, "រកមិនឃើញការកម្ម៉ង់សម្រាប់ថ្ងៃនេះទេ! (No orders found for today!)")
            return

        # Using Gemini 1.5 Pro for better Khmer accuracy
        model = ai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        Extract and sum all food orders from this text for today. 
        Format as a clean Khmer table with 'Dish' and 'Quantity'. 
        Calculate the 'Total Rice (សរុបបាយ)' at the bottom.
        Data: {daily_text}
        """

        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Error: AI is having trouble accessing the daily history.")

# --- 3. Start Both Services ---
if __name__ == "__main__":
    # Start web server thread
    t = Thread(target=run_web)
    t.start()
    
    print("Bot is starting...")
    # infinity_polling handles network drops better
    bot.infinity_polling()
