import telebot
from terabox_downloader import TeraboxDownloader

TOKEN = "8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs"
bot = telebot.TeleBot(TOKEN)

downloader = TeraboxDownloader()

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

    try:
        data = downloader.get_video_info(url)
        video_url = data["download_link"]

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

    except Exception as e:
        bot.reply_to(message, "Failed to extract video.")

print("Bot is running...")
bot.infinity_polling()
