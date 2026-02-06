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

# Constants
PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"
CHANNEL_USERNAME = "@terabox_directlinks"
CHANNEL_LINK = "https://t.me/terabox_directlinks"
SOURCE_GROUP = "@terabox_movies_hub0"
TARGET_CHANNEL = "@terabox_directlinks"

# Safety Check
if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("CRITICAL: BOT_TOKEN or XAPIVERSE_KEY is missing!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. HELPER FUNCTIONS ---

def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
        return False

def get_link_data(url):
    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url}
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            json_data = response.json()
            file_list = json_data.get("list", [])
            
            if file_list:
                info = file_list[0]
                fast = info.get("fast_stream_url", {})
                
                watch = (
                    fast.get("720p") or 
                    fast.get("480p") or 
                    fast.get("360p") or 
                    info.get("stream_url") or 
                    info.get("download_link")
                )
                
                download = info.get("download_link")
                name = info.get("name", "File Ready")
                
                return name, watch, download
    except Exception as e:
        logger.error(f"API Request Error: {e}")
    
    return None, None, None

def create_keyboard(watch_url, download_url):
    markup = types.InlineKeyboardMarkup()
    
    if watch_url:
        encoded_watch = quote_plus(watch_url)
        final_player_url = f"{PLAYER_BASE}?url={encoded_watch}"
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=final_player_url))
    
    if download_url:
        markup.add(types.InlineKeyboardButton("⬇️ Download", url=download_url))
        
    return markup

# --- 3. AUTO-POSTING HANDLER ---

@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'])
def group_auto_post(message):
    if not message.text:
        return
        
    current_username = message.chat.username
    target_group_name = SOURCE_GROUP.replace('@', '')
    
    if not current_username or current_username.lower() != target_group_name.lower():
        return

    url_text = message.text.strip()
    if "terabox" not in url_text and "1024tera" not in url_text:
        return

    logger.info(f"Processing Auto-Post from {SOURCE_GROUP}")

    name, watch, download = get_link_data(url_text)
    
    if watch:
        markup = create_keyboard(watch, download)
        try:
            bot.send_message(
                chat_id=TARGET_CHANNEL,
                text=f"🎬 {name}\n\n▶️ Watch Online\n⬇️ Download",
                reply_markup=markup
            )
            logger.info(f"Successfully posted to {TARGET_CHANNEL}")
        except Exception as e:
            logger.error(f"Failed to post to channel: {e}")

# --- 4. PRIVATE CHAT HANDLER ---

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_chat(message):
    if not message.text:
        return

    user_id = message.from_user.id
    
    if not is_user_joined(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        bot.reply_to(
            message, 
            "🚫 **Access Denied!**\n\nYou must join our channel to use this bot.", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    url_text = message.text.strip()
    if "terabox" not in url_text and "1024tera" not in url_text:
        return

    status_msg = bot.reply_to(message, "⏳ *Processing Link...*", parse_mode="Markdown")
    
    name, watch, download = get_link_data(url_text)
    
    if watch:
        markup = create_keyboard(watch, download)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"✅ **Ready!**\n📦 `{name}`",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.edit_message_text(
            "❌ Failed to extract stream links.", 
            message.chat.id, 
            status_msg.message_id
        )

# --- 5. FIXED PRODUCTION RUNNER (ONLY PART CHANGED) ---

def run_bot():
    logger.info("Bot initializing...")
    
    try:
        bot.remove_webhook()
        time.sleep(2)
        bot.get_updates(offset=-1)  # clear pending updates
    except Exception as e:
        logger.warning(f"Webhook cleanup: {e}")

    while True:
        try:
            logger.info("Starting Polling...")
            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=10,
                skip_pending=True
            )
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
