import telebot
import requests
import os

BOT_TOKEN = os.getenv("8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs")
API_KEY = os.getenv("sk_8c0eeebef5d2e808af9e554ef1f6b908")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send your TeraBox link and I’ll fetch the video.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    link = message.text.strip()

    if "terabox" not in link:
        bot.reply_to(message, "Please send a valid TeraBox link.")
        return

    try:
        url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": API_KEY
        }
        data = {
            "url": link
        }

        response = requests.post(url, json=data, headers=headers)
        result = response.json()

        if result.get("status") == "success":
            file = result["list"][0]
            download_link = file["download_link"]
            name = file["name"]
            size = file["size_formatted"]

            bot.reply_to(
                message,
                f"🎬 {name}\n📦 Size: {size}\n\n⬇ Download:\n{download_link}"
            )
        else:
            bot.reply_to(message, "Failed to fetch video.")

    except:
        bot.reply_to(message, "Error processing link.")

print("Bot running...")
bot.infinity_polling()
