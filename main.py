import telebot
import requests
import os

BOT_TOKEN = os.getenv("8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs")
API_KEY = os.getenv("sk_8c0eeebef5d2e808af9e554ef1f6b908")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Send me a Terabox link.")

@bot.message_handler(func=lambda m: True)
def handle_link(msg):
    url = msg.text

    bot.reply_to(msg, "Processing your link...")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": API_KEY
        }
        data = {
            "url": url
        }

        response = requests.post(api_url, json=data, headers=headers)
        result = response.json()

        if result.get("list"):
            file = result["list"][0]
            download_link = file["download_link"]
            stream_link = file["stream_url"]

            bot.send_message(
                msg.chat.id,
                f"Download: {download_link}\nStream: {stream_link}"
            )
        else:
            bot.send_message(msg.chat.id, "Failed to extract link.")

    except Exception as e:
        bot.send_message(msg.chat.id, "Error processing link.")

bot.infinity_polling()
