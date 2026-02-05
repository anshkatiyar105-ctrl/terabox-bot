import os
import time
import logging
import requests
import telebot

# --- 1. CONFIGURATION & LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("CRITICAL: BOT_TOKEN or XAPIVERSE_KEY is missing!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. HELPER FUNCTIONS ---

def extract_download_data(data):
    try:
        # Main data block
        info = data.get("data", data)

        # Some APIs return list of files
        if isinstance(info, list) and len(info) > 0:
            info = info[0]

        # Try different possible structures
        file_name = (
            info.get("file_name")
            or info.get("filename")
            or info.get("name")
            or "Unknown File"
        )

        size = (
            info.get("size")
            or info.get("filesize")
            or info.get("file_size")
            or "Unknown Size"
        )

        # Try all possible download link fields
        dl_link = (
            info.get("direct_link")
            or info.get("download_link")
            or info.get("url")
        )

        # Check nested download object
        if not dl_link:
            download = info.get("download", {})
            if isinstance(download, dict):
                dl_link = download.get("url") or download.get("link")

        # Final fallback
        if not dl_link:
            return "❌ Download link not found in API response."

        message = (
            f"📦 File: {file_name}\n"
            f"⚖️ Size: {size}\n\n"
            f"🚀 Direct Download Link:\n{dl_link}"
        )
        return message

    except Exception as e:
        logger.error(f"Parsing error: {e}")
        return "⚠️ Could not parse file data."

# --- 3. BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🚀 **Terabox Downloader**\n\nSend me a Terabox link to get the direct download data.")

@bot.message_handler(func=lambda message: True)
def handle_terabox_link(message):
    url = message.text.strip()
    
    if "terabox" not in url and "1024tera" not in url:
        bot.reply_to(message, "❌ Please send a valid Terabox link.")
        return

    status_msg = bot.reply_to(message, "⏳ Fetching secure link from xAPIverse...")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url}

        response = requests.post(api_url, headers=headers, json=payload, timeout=40)
        
        if response.status_code == 200:
            full_data = response.json()
            # Extract only the necessary info to avoid MESSAGE_TOO_LONG error
            clean_message = extract_download_data(full_data)
            
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=clean_message,
                parse_mode="Markdown"
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"❌ **API Error ({response.status_code})**"
            )

    except Exception as e:
        logger.error(f"Request Error: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="⚠️ An error occurred while processing the link."
        )

# --- 4. PRODUCTION POLLING LOOP ---

def run_bot():
    logger.info("Starting bot...")
    
    # Clean conflict: Remove webhook and wait
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        logger.warning(f"Webhook removal failed: {e}")

    while True:
        try:
            logger.info("Bot is now polling.")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5) # Cooldown before restart

if __name__ == "__main__":
    run_bot()
