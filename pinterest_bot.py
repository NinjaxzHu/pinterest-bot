import os
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Bot token environment variable se lenge (SAFE!)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SAVE_PATH = "/tmp/pinterest"
HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 12; Mobile)"}
PINIMG_REGEX = r"https://i\.pinimg\.com/originals/[a-z0-9/]+\.(jpg|jpeg|png|webp)"

def ensure_folder():
    os.makedirs(SAVE_PATH, exist_ok=True)

def extract_images(pin_url):
    resp = requests.get(pin_url, headers=HEADERS, timeout=15)
    if resp.status_code != 200:
        raise Exception("Page load failed")
    
    final_urls = []
    for match in re.finditer(PINIMG_REGEX, resp.text):
        final_urls.append(match.group(0))
    
    return list(set(final_urls))

def download_image(img_url):
    name = img_url.split("/")[-1]
    path = os.path.join(SAVE_PATH, name)
    
    r = requests.get(img_url, headers=HEADERS, stream=True, timeout=20)
    if r.status_code == 200:
        with open(path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return path
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📌 *Pinterest Image Downloader*\n\n"
        "🖼 Original Quality Download\n"
        "🎯 No Watermark\n\n"
        "📝 *How to use:*\n"
        "Just send me any Pinterest link!\n\n"
        "Example:\n"
        "`https://pin.it/xxxxx`\n\n"
        "Made by @ninjaxz_07"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    
    if not ("pinterest.com" in msg or "pin.it" in msg):
        await update.message.reply_text(
            "❌ Please send a Pinterest link!\n\n"
            "Example: https://pin.it/xxxxx"
        )
        return
    
    status = await update.message.reply_text("🔍 Searching images...")
    
    try:
        urls = extract_images(msg)
        
        if not urls:
            await status.edit_text("❌ No images found!")
            return
        
        await status.edit_text(f"✅ Found {len(urls)} image(s)!\n📥 Sending...")
        
        ensure_folder()
        sent = 0
        
        for i, img_url in enumerate(urls, 1):
            try:
                path = download_image(img_url)
                if path and os.path.exists(path):
                    with open(path, 'rb') as photo:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=f"📌 {i}/{len(urls)} - Original Quality"
                        )
                    sent += 1
                    os.remove(path)
            except:
                continue
        
        if sent > 0:
            await status.edit_text(f"✅ Sent {sent}/{len(urls)} images!")
        else:
            await status.edit_text("❌ Download failed!")
            
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found!")
        return
    
    print("🤖 Starting bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot is running 24/7!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    ensure_folder()
    main()
