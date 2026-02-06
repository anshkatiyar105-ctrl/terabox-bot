Youimport os
import time
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus

# --- CONFIGURATION & LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

# Constants
CHANNEL_USER = "@terabox_directlinks"
CHANNEL_LINK = "https://t.me/terabox_directlinks"
SOURCE_GROUP = "@terabox_movies_hub0"
TARGET_CHANNEL = "@terabox_directlinks"
PLAYER_BASE = "https://teraplayer979.github.io/stream-player/"

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("Missing BOT_TOKEN or XAPIVERSE_KEY. Exiting.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- HELPER FUNCTIONS ---

def check_sub(user_id):
    """Verifies if the user is in the required channel."""
    try:
        member = bot.get_chat_member(CHANNEL_USER, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        return False

def get_api_data(url):
    """Calls xAPIverse and extracts stream/download links safely."""
    try:
        api_endpoint = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": url}
        response = requests.post(api_endpoint, headers=headers, json=payload, timeout=40)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("list", [])
            if not items:
                return None
            
            file_info = items[0]
            name = file_info.get("name", "File Ready")
            fast = file_info.get("fast_stream_url", {})
            
            # Priority: 720p -> 480p -> 360p -> stream_url -> download_link
            stream = (
                fast.get("720p") or 
                fast.get("480p") or 
                fast.get("360p") or 
                file_info.get("stream_url") or 
                file_info.get("download_link")
            )
            download = file_info.get("download_link")
            
            return {"name": name, "stream": stream, "download": download}
    except Exception as e:
        logger.error(f"API Error: {e}")
    return None

# --- HANDLERS ---

# 1. Auto Posting Handler (Source Group Only)
@bot.message_handler(func=lambda m: m.chat.type in ['group', 'supergroup'] and m.chat.username == SOURCE_GROUP.replace('@', ''))
def group_handler(message):
    if not message.text:
        return
    
    url_text = message.text.strip()
    if "terabox" not in url_text and "1024tera" not in url_text:
        return
    
    logger.info(f"Auto-post trigger in {SOURCE_GROUP}")
    res = get_api_data(url_text)
    
    if res and res['stream']:
        encoded_url = quote_plus(res['stream'])
        player_url = f"{PLAYER_BASE}?url={encoded_url}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player_url))
        if res['download']:
            markup.add(types.InlineKeyboardButton("⬇️ Download", url=res['download']))
            
        try:
            bot.send_message(
                TARGET_CHANNEL,
                f"🎬 {res['name']}\n\n▶️ Watch Online\n⬇️ Download",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"Post to channel failed: {e}")

# 2. Private Chat Handler
@bot.message_handler(func=lambda m: m.chat.type == 'private')
def private_handler(message):
    if not message.text:
        return
    
    user_id = message.from_user.id
    url_text = message.text.strip()

    # Force Subscribe Check
    if not check_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        bot.reply_to(
            message, 
            "🚫 **Access Denied**\n\nYou must join our channel to use this bot.",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        return

    if "terabox" not in url_text and "1024tera" not in url_text:
        return

    status_msg = bot.reply_to(message, "⏳ *Generating links...*", parse_mode="Markdown")
    
    res = get_api_data(url_text)
    if not res:
        bot.edit_message_text("❌ Failed to fetch data. Link might be invalid.", message.chat.id, status_msg.message_id)
        return

    if res['stream']:
        encoded_url = quote_plus(res['stream'])
        player_url = f"{PLAYER_BASE}?url={encoded_url}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player_url))
        if res['download']:
            markup.add(types.InlineKeyboardButton("⬇️ Download", url=res['download']))
            
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"✅ **Ready!**\n\n📦 `{res['name']}`",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.edit_message_text("❌ No playable stream found.", message.chat.id, status_msg.message_id)

# --- BOT RUNNER ---

def run_bot():
    logger.info("Bot starting...")
    
    # Pre-start: Clean Conflict
    try:
        bot.remove_webhook()
        time.sleep(2)
    except:
        pass

    while True:
        try:
            logger.info("Polling...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
