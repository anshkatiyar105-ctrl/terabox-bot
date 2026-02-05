import telebot
import requests

TOKEN = "8469056505:AAHykdxXeNfLYOEQ85ETsPXJv06ZoP6Q0fs"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send your Terabox link and I’ll generate a download button.")

@bot.message_handler(func=lambda m: True)
def handle(message):
    url = message.text.strip()

    if "terabox" not in url.lower():
        bot.reply_to(message, "Please send a valid Terabox link.")
        return

    bot.reply_to(message, "Processing your link...")

    try:
        # Real public API (example working endpoint)
        api = f"https://terabox-api.vercel.app/api?url={url}"
        res = requests.get(api).json()

        if "download" in res:
            video_url = res["download"]

            markup = telebot.types.InlineKeyboardMarkup()
            btn = telebot.types.InlineKeyboardButton(
                "▶ Play / Download",
                url=video_url
            )
            markup.add(btn)

            bot.send_message(
                message.chat.id,
                "Your video is ready:",
                reply_markup=markup
            )
        else:
            bot.reply_to(message, "Could not extract video.")

    except:
        
        bot.reply_to(message, "Error processing the link.")

print("Bot is running...")
bot.infinity_polling()
