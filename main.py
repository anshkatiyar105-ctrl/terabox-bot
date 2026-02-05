import os
import time
import logging
import requests
import telebot

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("Missing BOT_TOKEN or XAPIVERSE_KEY")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)


def format_size(size_bytes):
    try:
        size_bytes = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
    except:
        return "Unknown Size"


def extract_data(data):
    try:
        info = data.get("data", {}) if isinstance(data.get("data"), dict) else data

        file_name = info.get("file_name") or info.get("filename") or "File"
        size = format_size(info.get("size") or info.get("filesize") or 0)

        link = (
            info.get("download_link")
            or info.get("direct_link")
            or info.get("dlink")
            or info.get("url")
        )

        if not link:
            return "❌ Download link not found."

        return (
            f"✅ **Download Ready**\n\n"
            f"📦 **File:** `{file_name}`\n"
            f"⚖️ **Size:** {size}\n\n"
            f"🚀 **Link:**\n`{link}`"
        )

    except Exception as e:
        logger.error(f"Parse error: {e}")
        return "⚠️ Failed to read API response."


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send any Terabox link.")


@bot.message_handler(func=lambda m: True)
def handle(message):
    url = message.text.strip()

    if "terabox" not in url:
        bot.reply_to(message, "Send a valid Terabox link.")
        return

    status = bot.reply_to(message, "Processing...")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url}

        r = requests.post(api_url, headers=headers, json=payload, timeout=60)

        if r.status_code == 200:
            data = r.json()
            msg = extract_data(data)
        else:
            msg = f"❌ API error: {r.status_code}"

        bot.edit_message_text(
            msg,
            message.chat.id,
            status.message_id,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(e)
        bot.edit_message_text(
            "⚠️ Internal error.",
            message.chat.id,
            status.message_id
        )


def run():
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling()


if __name__ == "__main__":
    run()
