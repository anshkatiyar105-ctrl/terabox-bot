import os
import time
import logging
import requests
import telebot
from telebot import apihelper

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

# --- 2. DATA EXTRACTION LOGIC ---

def safe_extract(data):
    """
    Defensive parser for xAPIverse JSON. 
    Protects against MESSAGE_TOO_LONG and attribute errors.
    """
    try:
        # Step 1: Locate the core info block
        # Some APIs wrap in 'data', others in 'result', some are flat
        info = data.get("data", {}) if isinstance(data.get("data"), dict) else data
        
        # Step 2: Extraction with multiple fallback keys
        name = info.get("file_name") or info.get("filename") or info.get("title") or "Unknown File"
        size = info.get("size") or info.get("filesize") or "Unknown Size"
        
        # Look for download link in various common nested structures
        dl_link = info.get("direct_link") or info.get("download_link") or info.get("url")
        if not dl_link and isinstance(info.get("download"), dict):
            dl_link = info.get("download", {}).get("url")
            
        if not dl_link:
            logger.warning(f"Link missing in JSON structure: {data}")
            return "❌ Direct download link not found in the API response."

        # Step 3: Length Protection (Telegram limit is 4096)
        # We truncate names if they are absurdly long
        if len(name) > 100: name = name[:97] + "..."
            
        message = (
            f"📦 **File:** `{name}`\n"
            f"⚖️ **Size:** {size}\n\n"
            f"🚀 **Direct Link:**\n`{dl_link}`"
        )
        
        # Final safety check on total length
        return message[:4000]

    except Exception as e:
        logger.error(f"Safe Parse Error: {e} | Data received: {data}")
        return "⚠️ Error parsing file data. The structure might have changed."

# --- 3. BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "✅ **Terabox Downloader Online**\nSend me a Terabox link to begin.")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    text = message.text.strip()
    
    # Simple Domain Check
    if "terabox" not in text and "1024tera" not in text:
        return # Ignore non-terabox messages

    status_msg = bot.reply_to(message, "⏳ *Generating direct link...*", parse_mode="Markdown")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": text}

        response = requests.post(api_url, headers=headers, json=payload, timeout=45)
        
        if response.status_code == 200:
            json_data = response.json()
            
            # If API reports internal error
            if json_data.get("status") == "error":
                response_text = f"❌ **API Error:** {json_data.get('message', 'Access Denied')}"
            else:
                response_text = safe_extract(json_data)
        else:
            logger.error(f"API HTTP Error: {response.status_code}")
            response_text = f"❌ **Server Error:** ({response.status_code})"

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=response_text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Handler Crash Prevented: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text="⚠️ Service temporarily unavailable."
        )

# --- 4. PRODUCTION ENGINE ---

def start_bot():
    """
    Clears webhooks to prevent 409 Conflict and enters a restart loop.
    """
    logger.info("Bot initializing...")
    
    # 1. Clean Conflict Start
    try:
        bot.remove_webhook()
        time.sleep(2) # Buffer for Railway environment to settle
    except Exception as e:
        logger.warning(f"Initial webhook clear failed: {e}")

    # 2. Infinite Polling Loop
    while True:
        try:
            logger.info("Polling started...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(10) # Cooldown before auto-restart

if __name__ == "__main__":
    start_bot()
