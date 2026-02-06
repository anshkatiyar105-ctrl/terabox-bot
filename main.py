import os
import time
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

CHANNEL_USERNAME = "@terabox_directlinks"
CHANNEL_LINK = "https://t.me/terabox_directlinks"

SOURCE_GROUP = "@terabox_movies_hub0"
TARGET_CHANNEL = "@terabox_directlinks"

PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("Missing BOT_TOKEN or XAPIVERSE_KEY")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


# ---------------- HELPERS ----------------
def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def join_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    return markup


def get_terabox_data(url):
    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url}

        response = requests.post(api_url, headers=headers, json=payload, timeout=40)

        if response.status_code != 200:
            return None

        data = response.json()
        file_list = data.get("list", [])
        if not file_list:
            return None

        info = file_list[0]
        fast = info.get("fast_stream_url", {})

        watch = (
            fast.get("720p")
            or fast.get("480p")
            or fast.get("360p")
            or info.get("stream_url")
            or info.get("download_link")
        )

        download = info.get("download_link")
        name = info.get("name", "Movie")

        return name, watch, download

    except Exception as e:
        logger.error(f"API error: {e}")
        return None


# ---------------- AUTO POST ----------------
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def auto_post(message):
    if not message.text:
        return

    if not message.chat.username:
        return

    if message.chat.username.lower() != SOURCE_GROUP.replace("@", "").lower():
        return

    url = message.text.strip()
    if "terabox" not in url and "1024tera" not in url:
        return

    result = get_terabox_data(url)
    if not result:
        return

    name, watch, download = result
    encoded_watch = quote_plus(watch)
    player_url = f"{PLAYER_BASE}?url={encoded_watch}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player_url))

    if download:
        markup.add(types.InlineKeyboardButton("⬇️ Download", url=download))

    bot.send_message(
        TARGET_CHANNEL,
        f"🎬 {name}\n\n▶️ Watch Online\n⬇️ Download",
        reply_markup=markup
    )


# ---------------- PRIVATE HANDLER ----------------
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_handler(message):
    if not message.text:
        return

    user_id = message.from_user.id

    if not is_user_joined(user_id):
        bot.reply_to(
            message,
            "🚫 Join our channel first.",
            reply_markup=join_markup()
        )
        return

    url = message.text.strip()
    if "terabox" not in url and "1024tera" not in url:
        return

    status = bot.reply_to(message, "⏳ Generating...")

    result = get_terabox_data(url)
    if not result:
        bot.edit_message_text(
            "❌ Failed.",
            message.chat.id,
            status.message_id
        )
        return

    name, watch, download = result
    encoded_watch = quote_plus(watch)
    player_url = f"{PLAYER_BASE}?url={encoded_watch}"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player_url))

    if download:
        markup.add(types.InlineKeyboardButton("⬇️ Download", url=download))

    bot.edit_message_text(
        f"✅ Ready!\n\n📦 {name}",
        message.chat.id,
        status.message_id,
        reply_markup=markup
    )


# ---------------- RUNNER ----------------
def run_bot():
    logger.info("Starting bot...")

    while True:
        try:
            # Force remove webhook before polling
            bot.remove_webhook()
            time.sleep(2)

            bot.infinity_polling(skip_pending=True)

        except Exception as e:
            logger.error(f"Restarting after error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
