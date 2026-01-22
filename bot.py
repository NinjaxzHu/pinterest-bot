import telebot
import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

# --- CONFIGURATION ---
# Bot Token ko environment variable se fetch karein (security ke liye)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8471774303:AAFpmZgGLw1S7FtyZTlrvdGmcLHA1ZIKEUU")

# Initialize Bot
bot = telebot.TeleBot(BOT_TOKEN)

# --- PINTEREST ENGINE (Modified for Bot) ---
class PinterestEngine:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.pinterest.com/"
        }

    def get_media_data(self, pin_url):
        try:
            session = requests.Session()
            response = session.get(pin_url, headers=self.headers, allow_redirects=True)
            
            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # 1. Try Video
            video_snippet = soup.find("script", {"data-test-id": "video-snippet"})
            if video_snippet:
                json_data = json.loads(video_snippet.string)
                if "contentUrl" in json_data:
                    return {
                        "type": "video",
                        "url": json_data["contentUrl"],
                        "ext": ".mp4"
                    }

            # 2. Try Image
            og_image = soup.find("meta", property="og:image")
            if og_image:
                image_url = og_image["content"]
                hd_image_url = re.sub(r'/\d+x/', '/originals/', image_url)
                return {
                    "type": "image",
                    "url": hd_image_url,
                    "ext": ".jpg"
                }

            return None
        except:
            return None

# Initialize Engine
engine = PinterestEngine()

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🌟 *Welcome to Pinterest Elite Bot!* 🌟\n\n"
        "Just paste any Pinterest link (Post/Reel/Video), "
        "and I will download it for you in High Quality.\n\n"
        "🔥 *Powered by IG/@ninjaxz_07*"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    
    # Check if link is valid
    if "pinterest" in url.lower() or "pin.it" in url.lower():
        
        # 1. Notify User
        msg = bot.reply_to(message, "⏳ *Analyzing Link...*", parse_mode="Markdown")
        
        # 2. Get Data
        data = engine.get_media_data(url)
        
        if not data:
            bot.edit_message_text("❌ Media not found or Invalid Link.", chat_id=message.chat.id, message_id=msg.message_id)
            return

        # 3. Download & Send
        try:
            bot.edit_message_text(f"⬇️ Downloading {data['type']}...", chat_id=message.chat.id, message_id=msg.message_id)
            
            # Download file to memory (temp)
            file_content = requests.get(data['url']).content
            filename = f"temp_{int(time.time())}{data['ext']}"
            
            with open(filename, 'wb') as f:
                f.write(file_content)
            
            # Send to Telegram
            caption = f"✅ *Downloaded Successfully*\n\n👤 *Credit: IG/@ninjaxz_07*"
            
            with open(filename, 'rb') as f:
                if data['type'] == 'video':
                    bot.send_video(message.chat.id, f, caption=caption, parse_mode="Markdown")
                else:
                    bot.send_photo(message.chat.id, f, caption=caption, parse_mode="Markdown")
            
            # Cleanup (Delete temp file)
            os.remove(filename)
            bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
            
        except Exception as e:
            bot.edit_message_text(f"❌ Error sending file: {e}", chat_id=message.chat.id, message_id=msg.message_id)
            
    else:
        # Ignore non-pinterest messages or reply invalid
        pass

# --- START POLLING ---
if __name__ == "__main__":
    print("🤖 Bot is Running...")
    print("Checking for messages...")
    bot.infinity_polling()
