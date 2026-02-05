import urllib.parse
import os
import time
import logging
import requests
import telebot
import urllib.parse
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
XAPIVERSE_KEY = os.getenv("XAPIVERSE_KEY")

CHANNEL_USERNAME = "@terabox_directlinks"
PLAYER_BASE = "https://teraplayer979.github.io/stream-player/?url="

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# --- FORCE SUBSCRIBE CHECK ---
def is_user_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start(message):
    if not is_user_joined(message.from_user.id):
        bot.reply_to(
            message,
            f"🚫 Please join our channel first:\nhttps://t.me/{CHANNEL_USERNAME.replace('@','')}"
        )
        return

    bot.reply_to(message, "Send any Terabox link.")

# --- MAIN LINK HANDLER ---
@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url_text = message.text.strip()
    if "terabox" not in url_text and "1024tera" not in url_text:
        return

    wait_msg = bot.reply_to(message, "⏳ Generating your links...")

    try:
        api_url = "https://xapiverse.com/api/terabox"
        headers = {"Content-Type": "application/json", "xAPIverse-Key": XAPIVERSE_KEY}
        payload = {"url": url_text}

        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            json_data = response.json()
            
            file_info = json_data.get("list", [{}])[0]
            raw_stream_link = file_info.get("stream_url") or file_info.get("download_link")
            download_link = file_info.get("download_link")

            if raw_stream_link:
                encoded_stream = urllib.parse.quote_plus(raw_stream_link)
                
                base_player_url = "https://teraplayer979.github.io/stream-player/"
                watch_url = f"{base_player_url}?url={encoded_stream}"
                
                logger.info(f"DEBUG: Final Player URL -> {watch_url}")
                
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("▶️ Watch Online", url=watch_url))
                
                if download_link:
                    markup.add(InlineKeyboardButton("⬇️ Download", url=download_link))

                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=wait_msg.message_id,
                    text="✅ Links Ready!",
                    reply_markup=markup
                )
            else:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=wait_msg.message_id,
                    text="❌ Stream link not found."
                )
                
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text=f"❌ API Error: {response.status_code}"
            )

    except Exception as e:
        logger.error(f"Error in handle_link: {e}")
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text="⚠️ Something went wrong.")

            # Stream extraction
            stream_url = (
                file_data.get("stream_url")
                or file_data.get("stream_link")
            )

            # fallback to fast stream
            if not stream_url:
                fast_stream = file_data.get("fast_stream_url", {})
                stream_url = fast_stream.get("720p") or fast_stream.get("480p")

            if download_url:
                markup = InlineKeyboardMarkup()

                # Watch button using your player site
                if stream_url:
                    encoded_stream = urllib.parse.quote(stream_url, safe="")
                    player_url = PLAYER_BASE + encoded_stream

                    markup.add(
                        InlineKeyboardButton(
                            "▶️ Watch Online",
                            url=player_url
                        )
                    )

                # Download button
                markup.add(
                    InlineKeyboardButton(
                        "⬇️ Download",
                        url=download_url
                    )
                )

                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=wait_msg.message_id,
                    text="✅ Your links are ready:",
                    reply_markup=markup
                )
            else:
                bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=wait_msg.message_id,
                    text="❌ Download link not found."
                )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text=f"❌ API Error: {response.status_code}"
            )

    except Exception as e:
        logger.error(e)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text="⚠️ Error processing link."
        )

# --- SAFE STARTUP ---
def run():
    time.sleep(5)
    bot.remove_webhook()
    bot.infinity_polling()

if __name__ == "__main__":
    run()
