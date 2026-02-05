import os
import telebot
import requests

BOT_TOKEN = os.getenv("8469056505:AAF5sUmwOFivt2fQ4oJHxARZMiIgW2orXVI")
API_KEY = os.getenv("sk_8c0eeebef5d2e808af9e554ef1f6b908")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send me a Terabox link.")

@bot.message_handler(func=lambda m: True)
def handle_link(message):
    link = message.text.strip()

    url = "https://xapiverse.com/api/terabox"
    payload = {
        "url": link
    }
    headers = {
        "Content-Type": "application/json",
        "xAPIverse-Key": API_KEY
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()

        if "list" in data and len(data["list"]) > 0:
            download_link = data["list"][0]["download_link"]
            bot.reply_to(message, download_link)
        else:
            bot.reply_to(message, "Failed to extract link.")

    except Exception as e:
        bot.reply_to(message, "Error occurred.")

print("Bot started")
bot.infinity_polling()
