import telebot
import requests
import os

BOT_TOKEN = os.getenv("8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs")
API_KEY = os.getenv("sk_8c0eeebef5d2e808af9e554ef1f6b908")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send me a TeraBox link and I’ll fetch the video.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()

    api_url = "https://xapiverse.com/api/terabox"
    headers = {
        "Content-Type": "application/json",
        "xAPIVerse-Key": API_KEY
    }
    payload = {
        "url": url
    }

    try:
        res = requests.post(api_url, json=payload, headers=headers)
        data = res.json()

        if data.get("status") == "success":
            file = data["list"][0]
            download_link = file["download_link"]
            name = file["name"]
            size = file["size_formatted"]

            reply = f"📁 {name}\n📦 Size: {size}\n\n🔗 Download:\n{download_link}"
            bot.reply_to(message, reply)

        else:
            bot.reply_to(message, "Failed to fetch video.")

    except Exception as e:
        bot.reply_to(message, "Error processing link.")

bot.infinity_polling()
