import telebot
import os
from google import generativeai as ai

# Replace with your actual keys or use environment variables
bot = telebot.TeleBot("")
ai.configure("")

@bot.message_handler(commands=['sum'])
def summarize_orders(message):
    # Check if the user is actually replying to a message
    if not message.reply_to_message or not message.reply_to_message.text:
        bot.reply_to(message, "សូម help reply ទៅលើសារដែលមានបញ្ជីម្ហូប (Please reply to the text list).")
        return

    raw_text = message.reply_to_message.text
    
    model = ai.GenerativeModel('gemini-1.5-flash')
    # Specific prompt to ensure it stays in Khmer and sums correctly
    prompt = f"Summarize these Khmer food orders into a clean table and count the total rice (បាយ): {raw_text}"
    
    try:
        response = model.generate_content(prompt)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "Error: AI is having trouble processing this.")

bot.polling()
