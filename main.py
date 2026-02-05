import telebot
import requests

TOKEN = "8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs"
bot = telebot.TeleBot(TOKEN)

def get_cdn_link(url):
    try:
        api = f"https://terabox-downloader-api.vercel.app/api?url={url}"
        res = requests.get(api, timeout=15).json()

        if "download_url" in res:
            return res["download_url"]
        return None
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send your Terabox link to get direct video stream.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    url = message.text.strip()

    if "terabox" not in url.lower():
        bot.reply_to(message, "Please send a valid Terabox link.")
        return

    bot.reply_to(message, "Extracting video...")

    cdn_link = get_cdn_link(url)

    if cdn_link:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("▶ Play Video", url=cdn_link),
            telebot.types.InlineKeyboardButton("⬇ Download Video", url=cdn_link)
        )

        bot.send_message(
            message.chat.id,
            "Your video is ready:",
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "Failed to extract video. Try another link.")

print("Bot is running...")
bot.infinity_polling()
