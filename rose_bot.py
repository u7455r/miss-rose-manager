import os
import random
import re
import telebot
from telebot import types
from keep_alive import keep_alive

# আপনার দেওয়া নতুন এপিআই টোকেন
BOT_TOKEN = "8968939053:AAEhZOysxMiwMHMqsOSd-AgdODnOCC4wVI0"
bot = telebot.TeleBot(BOT_TOKEN)

# অটো-রিয়্যাকশন ইমোজি লিস্ট
REACTIONS = ["🔥", "👍", "❤️", "🎉", "⚡", "👏"]

# ওয়ার্নিং কাউন্টার
USER_WARNS = {}

def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# চারকোণা বাটনের কিবোর্ড মেনু
def get_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_help = types.KeyboardButton("📖 কমান্ড লিস্ট")
    btn_info = types.KeyboardButton("👤 আমার তথ্য (/id)")
    btn_admins = types.KeyboardButton("🛡️ অ্যাডমিন লিস্ট (/admins)")
    btn_rules = types.KeyboardButton("📜 রুলস")
    btn_group = types.KeyboardButton("➕ গ্রুপে এড করুন")
    btn_channel = types.KeyboardButton("📢 চ্যানেলে এড করুন")
    
    markup.add(btn_help, btn_info)
    markup.add(btn_admins, btn_rules)
    markup.add(btn_group, btn_channel)
    return markup

# ইনলাইন লিঙ্ক মেনু
def get_main_inline_menu(bot_username):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_add_group = types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_username}?startgroup=true")
    btn_add_channel = types.InlineKeyboardButton("📢 Add to Channel", url=f"https://t.me/{bot_username}?startchannel=true")
    markup.add(btn_add_group, btn_add_channel)
    return markup

# মেনু কমান্ড সেটআপ
try:
    bot.set_my_commands([
        types.BotCommand("start", "বট শুরু করুন"),
        types.BotCommand("help", "কমান্ড তালিকা দেখুন"),
        types.BotCommand("pin", "মেসেজ পিন করুন"),
        types.BotCommand("unpin", "মেসেজ আনপিন করুন"),
        types.BotCommand("purge", "মেসেজ মুছে ফেলুন"),
        types.BotCommand("broadcast", "জরুরি নোটিশ দিন"),
        types.BotCommand("admins", "অ্যাডমিন তালিকা"),
        types.BotCommand("id", "আইডি ও তথ্য দেখুন"),
        types.BotCommand("stats", "সদস্য সংখ্যা দেখুন")
    ])
except Exception as e:
    print(f"Menu Error: {e}")

# ১. /start কমান্ড
@bot.message_handler(commands=['start'])
def start_command(message):
    bot_info = bot.get_me()
    if message.chat.type == 'private':
        text = (
            f"হ্যালো **{message.from_user.first_name}**! 👋\n\n"
            "আমি সম্পূর্ণ ফ্রি গ্রুপ ম্যানেজমেন্ট ও অটোমেশন বট।\n"
            "গ্রুপের সদস্য নিয়ন্ত্রণ, পিন মেসেজ, অ্যান্টি-স্প্যাম লিংক ব্লকার ও চ্যানেল অটো-রিয়্যাকশনের জন্য আমাকে গ্রুপে যুক্ত করুন।"
        )
        bot.send_message(message.chat.id, text, reply_markup=get_reply_keyboard(), parse_mode='Markdown')
        bot.send_message(message.chat.id, "কুইক লিঙ্ক বাটন:", reply_markup=get_main_inline_menu(bot_info.username))
    else:
        bot.reply_to(message, "বট সক্রিয় রয়েছে! কমান্ড দেখতে /help লিখুন।")

# ২. কাস্টম বাটন হ্যান্ডলার
@bot.message_handler(func=lambda msg: msg.text in [
    "📖 কমান্ড লিস্ট", "👤 আমার তথ্য (/id)", "🛡️ অ্যাডমিন লিস্ট (/admins)", "📜 রুলস", "➕ গ্রুপে এড করুন", "📢 চ্যানেলে এড করুন"
])
def reply_buttons_handler(message):
    bot_info = bot.get_me()
    
    if message.text == "📖 কমান্ড লিস্ট":
        help_text = (
            "📋 **গ্রুপের সব কমান্ড:**\n\n"
            "🔹 `/pin` (রিপ্লাই করে) - মেসেজ পিন করুন\n"
            "🔹 `/unpin` (রিপ্লাই করে) - মেসেজ আনপিন করুন\n"
            "🔹 `/purge` (রিপ্লাই করে) - একসাথে অনেক মেসেজ ডিলিট\n"
            "🔹 `/broadcast [মেসেজ]` - পিনসহ জরুরি নোটিশ দেওয়া\n"
            "🔹 `/admins` - অ্যাডমিনদের তালিকা দেখা\n"
            "🔹 `/warn` (রিপ্লাই করে) - সতর্কবার্তা (৩ বার হলে অটো-মিউট)\n"
            "🔹 `/ban` (রিপ্লাই করে) - সদস্যকে ব্যান করা\n"
            "🔹 `/kick` (রিপ্লাই করে) - গ্রুপ থেকে রিমুভ করা\n"
            "🔹 `/mute` ও `/unmute` - কথা বলা বন্ধ বা চালু করা\n"
            "🔹 `/id` বা `/info` - নিজের বা অন্যের আইডি কার্ড\n"
            "🔹 `/stats` - গ্রুপের মোট সদস্য সংখ্যা"
        )
        bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

    elif message.text == "👤 আমার তথ্য (/id)":
        info = (
            f"👤 **আপনার প্রোফাইল তথ্য:**\n"
            f"• নাম: {message.from_user.first_name}\n"
            f"• ইউজারনেম: @{message.from_user.username or 'নাই'}\n"
            f"• টেলিগ্রাম আইডি: `{message.from_user.id}`"
        )
        bot.send_message(message.chat.id, info, parse_mode='Markdown')

    elif message.text == "🛡️ অ্যাডমিন লিস্ট (/admins)":
        bot.send_message(message.chat.id, "গ্রুপে গিয়ে `/admins` লিখলে অ্যাডমিনদের পুরো তালিকা চলে আসবে।")

    elif message.text == "📜 রুলস":
        bot.send_message(message.chat.id, "📜 গ্রুপে কোনো প্রকার লিঙ্ক দেওয়া এবং স্প্যামিং করা সম্পূর্ণ নিষেধ।")

    elif message.text == "➕ গ্রুপে এড করুন":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{bot_info.username}?startgroup=true"))
        bot.send_message(message.chat.id, "গ্রুপে এড করতে নিচের বাটনে চাপ দিন:", reply_markup=markup)

    elif message.text == "📢 চ্যানেলে এড করুন":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Add to Channel", url=f"https://t.me/{bot_info.username}?startchannel=true"))
        bot.send_message(message.chat.id, "চ্যানেলে এডমিন করতে নিচের বাটনে চাপ দিন:", reply_markup=markup)

# ৩. মেসেজ পিন ও আনপিন (/pin, /unpin)
@bot.message_handler(commands=['pin'])
def pin_msg(message):
    if message.chat.type == 'private':
        return
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ আপনি অ্যাডমিন নন!")
        return
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ যে মেসেজটি পিন করবেন তাতে রিপ্লাই দিয়ে `/pin` লিখুন।", parse_mode='Markdown')
        return
    try:
        bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id, disable_notification=False)
        bot.reply_to(message, "📌 মেসেজটি পিন করা হয়েছে!")
    except Exception:
        bot.reply_to(message, "❌ পিন করা যায়নি। বটের অ্যাডমিন পারমিশন চেক করুন।")

@bot.message_handler(commands=['unpin'])
def unpin_msg(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    try:
        if message.reply_to_message:
            bot.unpin_chat_message(message.chat.id, message.reply_to_message.message_id)
        else:
            bot.unpin_all_chat_messages(message.chat.id)
        bot.reply_to(message, "📌 মেসেজ আনপিন করা হয়েছে!")
    except Exception:
        pass

# ৪. বাল্ক মেসেজ ডিলিট বা পার্জ (/purge)
@bot.message_handler(commands=['purge'])
def purge_messages(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ যেখান থেকে মেসেজ মোছা শুরু করবেন, সেই মেসেজে রিপ্লাই দিয়ে `/purge` দিন।")
        return

    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    deleted = 0

    for msg_id in range(start_id, end_id + 1):
        try:
            bot.delete_message(message.chat.id, msg_id)
            deleted += 1
        except Exception:
            pass
    
    notice = bot.send_message(message.chat.id, f"🧹 সফলভাবে {deleted} টি মেসেজ মুছে ফেলা হয়েছে!")
    try:
        telebot.util.sleep(2)
        bot.delete_message(message.chat.id, notice.message_id)
    except Exception:
        pass

# ৫. জরুরি ব্রডকাস্ট নোটিশ (/broadcast)
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    
    text_content = message.text.replace("/broadcast", "").strip()
    if not text_content:
        bot.reply_to(message, "⚠️ নিয়ম: `/broadcast আপনার জরুরি নোটিশ`", parse_mode='Markdown')
        return

    announcement = (
        f"📢 **গ্রুপের জরুরি নোটিশ:**\n\n"
        f"{text_content}\n\n"
        f"👤 *প্রেরক:* [{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    )
    sent_msg = bot.send_message(message.chat.id, announcement, parse_mode='Markdown')
    try:
        bot.pin_chat_message(message.chat.id, sent_msg.message_id)
    except Exception:
        pass

# ৬. অ্যাডমিন তালিকা (/admins)
@bot.message_handler(commands=['admins'])
def list_admins(message):
    if message.chat.type == 'private':
        return
    try:
        administrators = bot.get_chat_administrators(message.chat.id)
        admin_list = "🛡️ **গ্রুপ অ্যাডমিনদের তালিকা:**\n\n"
        for admin in administrators:
            user = admin.user
            role = "👑 Owner" if admin.status == "creator" else "⭐ Admin"
            name = user.first_name
            username = f"(@{user.username})" if user.username else ""
            admin_list += f"• {role}: [{name}](tg://user?id={user.id}) {username}\n"
        
        bot.send_message(message.chat.id, admin_list, parse_mode='Markdown')
    except Exception:
        bot.reply_to(message, "অ্যাডমিন তালিকা আনতে সমস্যা হয়েছে।")

# ৭. আইডি কার্ড ও পরিসংখ্যান
@bot.message_handler(commands=['id', 'info'])
def get_user_id(message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    text = (
        f"📋 **ইউজার ডেটা কার্ড:**\n\n"
        f"• **নাম:** {target.first_name}\n"
        f"• **ইউজারনেম:** @{target.username or 'নাই'}\n"
        f"• **টেলিগ্রাম আইডি:** `{target.id}`"
    )
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def group_stats(message):
    if message.chat.type == 'private':
        return
    try:
        count = bot.get_chat_member_count(message.chat.id)
        bot.reply_to(message, f"📊 **গ্রুপ পরিসংখ্যান:**\nমোট সদস্য সংখ্যা: **{count}** জন")
    except Exception:
        pass

# ৮. সতর্কবার্তা (/warn)
@bot.message_handler(commands=['warn'])
def warn_user(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        bot.reply_to(message, "⚠️ রিপ্লাই দিন যাকে সতর্ক করবেন।")
        return

    target = message.reply_to_message.from_user
    key = f"{message.chat.id}_{target.id}"
    USER_WARNS[key] = USER_WARNS.get(key, 0) + 1
    current_warns = USER_WARNS[key]

    if current_warns >= 3:
        try:
            bot.restrict_chat_member(message.chat.id, target.id, permissions=types.ChatPermissions(can_send_messages=False))
            bot.reply_to(message, f"🚫 [{target.first_name}](tg://user?id={target.id}) ৩ বার সতর্কবার্তা পেয়েছেন। তাকে মিউট করা হলো!", parse_mode='Markdown')
            USER_WARNS[key] = 0
        except Exception:
            pass
    else:
        bot.reply_to(message, f"⚠️ [{target.first_name}](tg://user?id={target.id}) আপনাকে সতর্ক করা হলো!\nমোট ওয়ার্নিং: **{current_warns}/3**", parse_mode='Markdown')

# ৯. অ্যাডমিন মডারেশন: ব্যান, কিক, মিউট, আনমিউট
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    try:
        bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, "🚫 সদস্যকে ব্যান করা হয়েছে।")
    except Exception:
        bot.reply_to(message, "ব্যান করা যায়নি।")

@bot.message_handler(commands=['kick'])
def kick_user(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    try:
        bot.unban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        bot.reply_to(message, "👢 সদস্যকে গ্রুপ থেকে বের করা হয়েছে।")
    except Exception:
        bot.reply_to(message, "কিক করা যায়নি।")

@bot.message_handler(commands=['mute'])
def mute_user(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    try:
        bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, permissions=types.ChatPermissions(can_send_messages=False))
        bot.reply_to(message, "🔇 সদস্যকে মিউট করা হয়েছে।")
    except Exception:
        bot.reply_to(message, "মিউট করা যায়নি।")

@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if message.chat.type == 'private' or not is_admin(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message:
        return
    try:
        bot.restrict_chat_member(
            message.chat.id, 
            message.reply_to_message.from_user.id, 
            permissions=types.ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
        )
        bot.reply_to(message, "🔊 আনমিউট করা হয়েছে।")
    except Exception:
        bot.reply_to(message, "আনমিউট করা যায়নি।")

@bot.message_handler(commands=['rules'])
def send_rules(message):
    rules = (
        "📜 **গ্রুপের নিয়মাবলী:**\n\n"
        "১. স্প্যাম মেসেজ ও লিঙ্ক শেয়ার করা সম্পূর্ণ নিষেধ।\n"
        "২. একে অপরকে সম্মান দিন।"
    )
    bot.reply_to(message, rules, parse_mode='Markdown')

# ১০. অটো অ্যান্টি-স্প্যাম লিংক ব্লকার
@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def auto_anti_link(message):
    link_pattern = r'(https?://[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+)'
    if re.search(link_pattern, message.text or ''):
        if not is_admin(message.chat.id, message.from_user.id):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"⚠️ [{message.from_user.first_name}](tg://user?id={message.from_user.id}), গ্রুপে লিঙ্ক দেওয়া সম্পূর্ণ নিষেধ!", parse_mode='Markdown')
            except Exception:
                pass

# ১১. স্বাগতম বার্তা
@bot.message_handler(content_types=['new_chat_members'])
def welcome_member(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            bot.reply_to(message, "ধন্যবাদ আমাকে যুক্ত করার জন্য! গ্রুপ নিয়ন্ত্রণে অ্যাডমিন পারমিশন দিন।")
            continue
        bot.send_message(
            message.chat.id,
            f"👋 স্বাগতম [{member.first_name}](tg://user?id={member.id}) আমাদের গ্রুপে!\n🆔 আইডি: `{member.id}`\n\nগ্রুপের তথ্য জানতে `/stats` ও নিয়ম দেখতে `/rules` লিখুন।",
            parse_mode='Markdown'
        )

# ১২. চ্যানেলে অটো-রিয়্যাকশন
@bot.channel_post_handler(func=lambda msg: True)
def channel_reaction(message):
    try:
        bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[types.ReactionTypeEmoji(random.choice(REACTIONS))],
            is_big=False
        )
    except Exception:
        pass

# ১৩. প্রাইভেট চ্যাটে স্বাভাবিক কথা বলা
@bot.message_handler(func=lambda msg: msg.chat.type == 'private')
def smart_reply(message):
    text = message.text.lower()
    name = message.from_user.first_name

    if any(g in text for g in ["hi", "hello", "হাই"]):
        bot.reply_to(message, f"হ্যালো {name}! কেমন আছেন? 😊")
    elif any(k in text for k in ["kemon acho", "কেমন আছো"]):
        bot.reply_to(message, "আলহামদুলিল্লাহ, আমি খুব ভালো আছি! ❤️")
    elif any(q in text for q in ["ki koro", "কি করো"]):
        bot.reply_to(message, "গ্রুপ পাহারা দিচ্ছি আর সবার সাথে গল্প করছি! 🤖")
    elif any(b in text for b in ["bye", "বিদায়"]):
        bot.reply_to(message, f"বিদায় {name}! ভালো থাকবেন। 👋")
    else:
        bot.reply_to(message, f"বার্তা পেয়েছি {name}! কমান্ড দেখতে /help লিখুন। ✨")

if __name__ == '__main__':
    keep_alive()
    print("Rose Bot is fully active...")
    bot.infinity_polling()
