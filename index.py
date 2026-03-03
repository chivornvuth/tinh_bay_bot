import os
import telebot
from flask import Flask
from threading import Thread
import google.generativeai as ai

# --- 1. Keep-Alive Web Server for Render ---
# Render requires an active port to keep the free service running.
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    # Render uses port 10000 by default for web services
    app.run(host='0.0.0.0', port=10000)

# --- 2. Bot Configuration ---
# These pull from the "Environment Variables" you set in the Render dashboard
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai.configure(api_key=GEMINI_KEY)

@bot.message_handler(commands=['sum'])
def summarize_orders(message):
    # Check if the user is actually replying to a message
    if not message.reply_to_message or not message.reply_to_message.text:
        bot.reply_to(message, "សូម help reply ទៅលើសារដែលមានបញ្ជីម្ហូប (Please reply to the text list).")
        return

    raw_text = message.reply_to_message.text
    
    # Using Gemini 1.5 Flash for speed
    model = ai.GenerativeModel('gemini-1.5-flash')
    
    # Specific prompt to ensure it stays in Khmer and sums correctly
    prompt = f"Summarize these Khmer food orders into a clean table and count the total rice (បាយ): {raw_text}"
    
    try:
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Error: AI is having trouble processing this.")

# --- 3. Start Both Services ---
if __name__ == "__main__":
    # Start the Flask server in a separate thread so it doesn't block the bot
    t = Thread(target=run_web)
    t.start()
    
    print("Bot is starting...")
    # infinity_polling is better for production as it handles network drops
    bot.infinity_polling()
