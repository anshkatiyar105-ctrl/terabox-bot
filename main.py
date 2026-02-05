import telebot

TOKEN = "PASTE_YOUR_TOKEN_HERE"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Send your Terabox link and I’ll generate a download button."
    )

@bot.message_handler(func=lambda m: True)
def handle(message):
    url = message.text.strip()

    if "terabox" not in url.lower():
        bot.reply_to(message, "Please send a valid Terabox link.")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton(
        "▶ Open & Download",
        url=url
    )
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "Your link is ready:",
        reply_markup=markup
    )

print("Bot is running...")
bot.infinity_polling()
