import os
import time
import logging
import requests
import telebot
from telebot import types
from urllib.parse import quote_plus

# --- CONFIGURATION ---
# Set these in your Railway Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID") # e.g., "@MyChannelUsername" or -100123456789
CHANNEL_LINK = os.getenv("CHANNEL_LINK") # e.g., "https://t.me/MyChannelUsername"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if not BOT_TOKEN or not XAPIVERSE_KEY or not CHANNEL_ID:
    logger.error("Missing required environment variables!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- HELPERS ---

def is_subscribed(user_id):
    """Checks if the user is a member of the required channel."""
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        # Statuses that count as 'joined'
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
    return False

def get_force_subscribe_markup():
    """Returns the markup for the subscription requirement message."""
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)
    markup.add(btn)
    return markup

# --- HANDLERS ---

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, "👋 Welcome! Send me a Terabox link and I'll generate your player link.")

@bot.message_handler(func=lambda message: True)
def handle_terabox_request(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # 1. Check Force Subscribe
    if not is_subscribed(user_id):
        bot.send_message(
            message.chat.id, 
            "⚠️ **Access Denied!**\n\nYou must join our channel to use this bot.",
            parse_mode="Markdown",
            reply_markup=get_force_subscribe_markup()
        )
        return

    # 2. Validate Link
    if "terabox" not in text and "1024tera" not in text:
        bot.reply_to(message, "❌ Please send a valid Terabox link.")
        return

    status_msg = bot.reply_to(message, "⏳ *Generating your player link...*", parse_mode="Markdown")

    try:
        # 3. Call xAPIverse API
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": text}
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            json_data = response.json()
            
            # Extract data safely (assuming list[0] structure)
            file_info = json_data.get("list", [{}])[0]
            stream_link = file_info.get("stream_url") or file_info.get("download_link")
            download_link = file_info.get("download_link")

            if stream_link:
                # --- THE FIX: URL ENCODING ---
                encoded_stream = quote_plus(stream_link)
                player_base = "https://teraplayer979.github.io/stream-player/"
                final_watch_url = f"{player_base}?url={encoded_stream}"
                
                # Debugging log for Railway
                logger.info(f"Generated Watch URL: {final_watch_url}")

                # 4. Create Buttons
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=final_watch_url))
                if download_link:
                    markup.add(types.InlineKeyboardButton("⬇️ Download File", url=download_link))

                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=status_msg.message_id,
                    text="✅ **Links Generated Successfully!**",
                    reply_markup=markup
                )
            else:
                bot.edit_message_text(message.chat.id, status_msg.message_id, "❌ No stream/download link found in API response.")
        else:
            bot.edit_message_text(message.chat.id, status_msg.message_id, f"❌ API Error: {response.status_code}")

    except Exception as e:
        logger.error(f"Error processing link: {e}")
        bot.edit_message_text(message.chat.id, status_msg.message_id, "⚠️ An unexpected error occurred.")

# --- RUNNER ---

def run_bot():
    logger.info("Bot is starting...")
    # Clean webhook conflict
    try:
        bot.remove_webhook()
        time.sleep(2)
    except:
        pass

    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Polling crashed: {e}")
            time.sleep(10) # Cooldown before restart

if __name__ == "__main__":
    run_bot()
