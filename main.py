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
# CHANNEL_ID can now be "@your_username"
CHANNEL_ID = os.getenv("CHANNEL_ID", "@terabox_directlinks")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/terabox_directlinks")

if not BOT_TOKEN or not XAPIVERSE_KEY:
    logger.error("CRITICAL: BOT_TOKEN or XAPIVERSE_KEY is missing!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- 2. FORCE SUBSCRIBE LOGIC ---

def check_membership(user_id):
    """
    Checks membership using a username or numeric ID.
    Bot must be an Admin in the channel.
    """
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        # Valid statuses: member, administrator, or creator
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
    return False

def get_join_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
    return markup

# --- 3. BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    bot.reply_to(message, "👋 Welcome! Send me a Terabox link and I'll generate the bypass links for you.")

@bot.message_handler(func=lambda message: True)
def handle_terabox(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Step 1: Force Subscribe Check
    if not check_membership(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ **Access Denied!**\n\nYou must join our channel to use this bot. After joining, send the link again.",
            parse_mode="Markdown",
            reply_markup=get_join_markup()
        )
        return

    # Step 2: Link Validation
    if "terabox" not in text and "1024tera" not in text:
        bot.reply_to(message, "❌ Please send a valid Terabox link.")
        return

    status_msg = bot.reply_to(message, "⏳ *Processing your link...*", parse_mode="Markdown")

    try:
        # Step 3: Call xAPIverse API
        api_url = "https://xapiverse.com/api/terabox"
        headers = {
            "Content-Type": "application/json",
            "xAPIverse-Key": XAPIVERSE_KEY
        }
        payload = {"url": text}
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            json_data = response.json()
            
            # Step 4: Extract from list[0]
            try:
                file_info = json_data.get("list", [])[0]
                stream_link = file_info.get("stream_url") or file_info.get("download_link")
                download_link = file_info.get("download_link")
                file_name = file_info.get("name", "File_Ready")

                if stream_link:
                    # Step 5: URL Encoding for Custom Player
                    encoded_link = quote_plus(stream_link)
                    player_url = f"https://teraplayer979.github.io/stream-player/?url={encoded_link}"
                    
                    # Create Buttons
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("▶️ Watch Online", url=player_url))
                    if download_link:
                        markup.add(types.InlineKeyboardButton("⬇️ Download", url=download_link))

                    bot.edit_message_text(
                        chat_id=message.chat.id,
                        message_id=status_msg.message_id,
                        text=f"✅ **Links Generated!**\n\n📦 `{file_name}`",
                        parse_mode="Markdown",
                        reply_markup=markup
                    )
                else:
                    bot.edit_message_text(message.chat.id, status_msg.message_id, "❌ Error: API did not return valid links.")
            except (IndexError, KeyError):
                bot.edit_message_text(message.chat.id, status_msg.message_id, "❌ API success but file data is missing.")
        else:
            bot.edit_message_text(message.chat.id, status_msg.message_id, f"❌ API Error: Code {response.status_code}")

    except Exception as e:
        logger.error(f"Critical error: {e}")
        bot.edit_message_text(message.chat.id, status_msg.message_id, "⚠️ Something went wrong. Connection timed out.")

# --- 4. PRODUCTION ENGINE (RAILWAY READY) ---

def start_bot():
    logger.info("Starting bot...")
    
    # Pre-start: Avoid 409 Conflict by clearing webhooks & adding delay
    try:
        bot.remove_webhook()
        time.sleep(3) # Vital for Railway redeployments
    except:
        pass

    while True:
        try:
            logger.info("Bot is polling...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Polling crash: {e}")
            time.sleep(10) # Cooldown before restart

if __name__ == "__main__":
    start_bot()
