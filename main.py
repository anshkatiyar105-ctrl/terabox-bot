import os
import time
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus

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

# --- 2. EXTRACTION LOGIC ---

def get_hls_link(file_info):
    """
    Strictly extracts HLS (.m3u8) links with quality priority.
    Does NOT return .mkv or direct download links.
    """
    fast_streams = file_info.get("fast_stream_url", {})
    if not isinstance(fast_streams, dict):
        return None
    
    # Priority Order: 720p -> 480p -> 360p
    priorities = ["720p", "480p", "360p"]
    for quality in priorities:
        link = fast_streams.get(quality)
        if link and (".m3u8" in link or "m3u8" in link.lower()):
            return link
    return None

# --- 3. BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    bot.reply_to(message, "👋 **Terabox HLS Downloader**\nSend me a link to get high-speed HLS streaming and download links.")

@bot.message_handler(func=lambda message: True)
def handle_terabox(message):
    text = message.text.strip()
    
    if "terabox" not in text and "1024tera" not in text:
        return

    status_msg = bot.reply_to(message, "⏳ *Processing HLS Stream...*", parse_mode="Markdown")

    try:
        # API Request
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": text}
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            json_data = response.json()
            
            # Safe parsing of the list[0] structure
            data_list = json_data.get("list", [])
            if not data_list:
                bot.edit_message_text("❌ No files found in this link.", message.chat.id, status_msg.message_id)
                return
            
            file_info = data_list[0]
            file_name = file_info.get("name", "File_Ready")
            download_url = file_info.get("download_link")
            
            # Get only HLS link
            hls_link = get_hls_link(file_info)
            
            markup = types.InlineKeyboardMarkup()
            
            # Watch Online Button (HLS ONLY)
            if hls_link:
                encoded_link = quote_plus(hls_link)
                player_url = f"https://teraplayer979.github.io/stream-player/?url={encoded_link}"
                markup.add(types.InlineKeyboardButton("▶️ Watch Online (HLS)", url=player_url))
            
            # Download Button
            if download_url:
                markup.add(types.InlineKeyboardButton("⬇️ Download File", url=download_url))

            if not hls_link and not download_url:
                bot.edit_message_text("❌ No playable or downloadable links available.", message.chat.id, status_msg.message_id)
                return

            response_text = f"✅ **Links Generated!**\n\n📦 `{file_name}`"
            if not hls_link:
                response_text += "\n\n⚠️ *Note: HLS Streaming not available for this file.*"

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=response_text,
                parse_mode="Markdown",
                reply_markup=markup
            )
            
        else:
            bot.edit_message_text(f"❌ API Error: {response.status_code}", message.chat.id, status_msg.message_id)

    except Exception as e:
        logger.error(f"Error: {e}")
        bot.edit_message_text("⚠️ An error occurred. The link might be expired or invalid.", message.chat.id, status_msg.message_id)

# --- 4. PRODUCTION RUNNER ---

def run_bot():
    logger.info("Bot is starting...")
    
    # Pre-start: Avoid 409 Conflict by clearing webhooks & adding delay
    try:
        bot.remove_webhook()
        time.sleep(3) # Vital for Railway redeployments
    except:
        pass

    while True:
        try:
            logger.info("Polling started.")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Polling crash: {e}")
            time.sleep(10) # Cooldown before restart

if __name__ == "__main__":
    run_bot()
