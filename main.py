import telebot
import requests
from flask import Flask, request
import os

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")
IMGBB_KEY = os.environ.get("IMGBB_KEY")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7936924851"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# /start বা /help কমান্ড (ইউজারের জন্য)
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    bot.reply_to(
        message,
        "👋 হ্যালো!\n\n"
        "📸 ছবি পাঠান ➝ আমি সেটি আপলোড করে direct link আপনাকে দিব।\n"
        "➡️ ছবিটা এডমিনও দেখতে পারবে।\n"
        "🔗 টেক্সট বা লিংক পাঠালে শুধু এডমিন পাবে।"
    )

# ছবি হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        username = message.from_user.username or "NoUsername"
        user_id = message.from_user.id

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        img_data = requests.get(file_url).content

        # imgbb এ আপলোড
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_KEY},
            files={"image": img_data}
        )
        data = res.json()

        if data["success"]:
            url = data["data"]["url"]
            viewer = data["data"]["url_viewer"]

            # ইউজারকে শুধুমাত্র লিংক দেখানো
            bot.send_message(
                message.chat.id,
                f"✅ ছবি আপলোড হয়েছে!\n🔗 Direct Link: {url}"
            )

            # এডমিনকে ফরওয়ার্ড করা
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
            chat_type = message.chat.type
            chat_info = f"👥 Group: {message.chat.title} (ID: {message.chat.id})" if chat_type in ["group", "supergroup"] else "👤 Private Chat"
            bot.send_message(
                ADMIN_ID,
                f"📤 New Upload\n👤 User: @{username} (ID: {user_id})\n{chat_info}"
            )
        else:
            bot.send_message(message.chat.id, "❌ Upload failed!")
    except Exception as e:
        print(f"Error: {e}")

# টেক্সট/লিংক হ্যান্ডলার
@bot.message_handler(content_types=['text'])
def handle_text(message):
    username = message.from_user.username or "NoUsername"
    user_id = message.from_user.id
    text = message.text

    chat_type = message.chat.type
    chat_info = f"👥 Group: {message.chat.title} (ID: {message.chat.id})" if chat_type in ["group", "supergroup"] else "👤 Private Chat"

    bot.send_message(
        ADMIN_ID,
        f"💬 New Message\n👤 User: @{username} (ID: {user_id})\n{chat_info}\n\n📩 {text}"
    )
    # ইউজারকে কিছু দেখাবে না

# Flask webhook setup
app = Flask(__name__)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    domain = os.environ.get("RENDER_EXTERNAL_URL")
    bot.set_webhook(url=f"{domain}/{BOT_TOKEN}")
    return "Webhook set!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
