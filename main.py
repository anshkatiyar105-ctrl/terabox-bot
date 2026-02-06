import os
import time
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------- ENV ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("Missing BOT_TOKEN or XAPIVERSE_KEY")
    exit(1)

# ---------------- CONSTANTS ----------------
PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"

CHANNEL_USER = "@terabox_directlinks"
CHANNEL_LINK = "https://t.me/terabox_directlinks"

SOURCE_GROUP = "terabox_movies_hub0"
TARGET_CHANNEL = "@terabox_directlinks"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------------- HELPERS ----------------
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USER, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


def get_api_data(url):
    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url}

        r = requests.post(api_url, headers=headers, json=payload, timeout=40)
        if r.status_code != 200:
            logger.error("API error: %s", r.status_code)
            return None

        data = r.json()
        items = data.get("list", [])
        if not items:
            return None

        info = items[0]
        name = info.get("name", "File")

        fast = info.get("fast_stream_url", {})
        stream = (
            fast.get("720p")
            or fast.get("480p")
            or fast.get("360p")
            or info.get("stream_url")
            or info.get("download_link")
        )

        download = info.get("download_link")

        return {
            "name": name,
            "stream": stream,
            "download": download
        }

    except Exception as e:
        logger.error("API crash: %s", e)
        return None


# ---------------- GROUP AUTO POST ----------------
@bot.message_handler(func=lambda m: m.chat.type in ["group", "supergroup"])
def group_handler(message):
    try:
        if not message.text:
            return

        if not message.chat.username:
            return

        if message.chat.username.lower() != SOURCE_GROUP.lower():
            return

        url = message.text.strip()
        if "terabox" not in url and "1024tera" not in url:
            return

        logger.info("Auto-post triggered")

        res = get_api_data(url)
        if not res or not res["stream"]:
            return

        encoded = quote_plus(res["stream"])
        player = f"{PLAYER_BASE}?url={encoded}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player))

        if res["download"]:
            markup.add(types.InlineKeyboardButton("⬇️ Download", url=res["download"]))

        bot.send_message(
            TARGET_CHANNEL,
            f"🎬 {res['name']}\n\n▶️ Watch Online\n⬇️ Download",
            reply_markup=markup
        )

    except Exception as e:
        logger.error("Group handler crash: %s", e)


# ---------------- PRIVATE HANDLER ----------------
@bot.message_handler(func=lambda m: m.chat.type == "private")
def private_handler(message):
    try:
        if not message.text:
            return

        logger.info("Private message received")

        user_id = message.from_user.id

        if not check_sub(user_id):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Join Channel", url=CHANNEL_LINK))
            bot.reply_to(message, "Join channel first.", reply_markup=markup)
            return

        url = message.text.strip()
        if "terabox" not in url and "1024tera" not in url:
            return

        msg = bot.reply_to(message, "Generating...")

        res = get_api_data(url)
        if not res:
            bot.edit_message_text("Failed to fetch link.", message.chat.id, msg.message_id)
            return

        encoded = quote_plus(res["stream"])
        player = f"{PLAYER_BASE}?url={encoded}"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player))

        if res["download"]:
            markup.add(types.InlineKeyboardButton("⬇️ Download", url=res["download"]))

        bot.edit_message_text(
            f"✅ Ready\n\n📦 {res['name']}",
            message.chat.id,
            msg.message_id,
            reply_markup=markup
        )

    except Exception as e:
        logger.error("Private handler crash: %s", e)


# ---------------- RUNNER ----------------
def run_bot():
    logger.info("Starting bot...")
    try:
        bot.remove_webhook()
    except:
        pass

    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error("Polling error: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    run_bot()
