import telebot
import requests

TOKEN = "8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs"
bot = telebot.TeleBot(TOKEN)

def extract_video(url):
    try:
        api = f"https://terabox-api-five.vercel.app/api?url={url}"
        res = requests.get(api, timeout=15).json()
        return res.get("download_url")
    except:
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send your Terabox link.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    url = message.text.strip()

    if "terabox" not in url.lower():
        bot.reply_to(message, "Please send a valid Terabox link.")
        return

    bot.reply_to(message, "Extracting video...")

    video_url = extract_video(url)

    if video_url:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("▶ Play Video", url=video_url),
            telebot.types.InlineKeyboardButton("⬇ Download Video", url=video_url)
        )

        bot.send_message(
            message.chat.id,
            "Your video is ready:",
            reply_markup=markup
        )
    else:
        bot.reply_to(message, "Failed to extract video.")

print("Bot is running...")
bot.infinity_polling()
