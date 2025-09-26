import telebot
import requests
from flask import Flask, request
import os

# Config
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Render secret
IMGBB_KEY = os.environ.get("IMGBB_KEY")  # Render secret
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7936924851"))  # Render secret

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# /start বা /help কমান্ড
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    bot.reply_to(
        message,
        "👋 হ্যালো!\n\n"
        "📸 ছবি পাঠান ➝ আমি সেটি imgbb তে আপলোড করে আপনাকে লিংক দিব।\n"
        "➡️ সাথে ছবি এডমিনের কাছে ফরওয়ার্ড হবে।\n\n"
        "🔗 যদি টেক্সট/লিংক পাঠান ➝ সেটিও এডমিন পাবে।\n\n"
        "✅ এই বট প্রাইভেট এবং গ্রুপে কাজ করে!"
    )

# ছবি হ্যান্ডলার
@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        username = message.from_user.username or "NoUsername"
        user_id = message.from_user.id

        # হাই রেজোলিউশন ফটো
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # ফটো ডাউনলোড
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

            # ইউজারকে লিংক পাঠানো
            bot.send_message(
                message.chat.id,
                f"✅ আপনার ছবি আপলোড হয়েছে!\n\n"
                f"🔗 Direct: {url}\n"
                f"🌐 Viewer: {viewer}"
            )

            # এডমিনকে ছবি ফরওয়ার্ড
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

            # এডমিনকে ইউজার ডিটেইলস
            chat_type = message.chat.type
            chat_info = f"👥 Group: {message.chat.title} (ID: {message.chat.id})" if chat_type in ["group", "supergroup"] else "👤 Private Chat"
            bot.send_message(
                ADMIN_ID,
                f"📤 New Upload\n"
                f"👤 User: @{username} (ID: {user_id})\n"
                f"{chat_info}\n\n"
                f"🔗 Direct: {url}\n"
                f"🌐 Viewer: {viewer}"
            )
        else:
            bot.reply_to(message, "❌ আপলোড ব্যর্থ হয়েছে!")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

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
        f"💬 New Message\n"
        f"👤 User: @{username} (ID: {user_id})\n"
        f"{chat_info}\n\n📩 {text}"
    )

    bot.reply_to(message, "✅ আপনার মেসেজ এডমিন এর কাছে পাঠানো হয়েছে!")

# Flask Webhook (Render-Ready)
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
    domain = os.environ.get("RENDER_EXTERNAL_URL")  # Render এ ডোমেইন অটো পাওয়া যাবে
    bot.set_webhook(url=f"{domain}/{BOT_TOKEN}")
    return "Webhook set!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
