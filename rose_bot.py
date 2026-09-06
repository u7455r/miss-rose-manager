import os
import sys
import time
import re
import sqlite3
import telebot
from telebot import types
from keep_alive import keep_alive

print("--- Initializing Rafim Rose Manager Ultimate Engine ---", flush=True)

BOT_TOKEN = "8886219226:AAGue3mFnx5NWCToUqTbkUxf9Ah_ThQ-YaQ"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

REQ_CHANNEL = "@rafimhossen3"
REQ_CHANNEL_LINK = "https://t.me/rafimhossen3"
DB_FILE = "rose_ultimate.db"

# Admin Tracking
ADMIN_USERNAME = "rafimhossen"
ADMIN_ID = None

# ==================== DATABASE INITIALIZATION ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER, PRIMARY KEY (chat_id, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS filters (chat_id INTEGER, keyword TEXT, reply TEXT, PRIMARY KEY (chat_id, keyword))''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, val INTEGER)''')
    conn.commit()
    conn.close()

init_db()

def get_admin_id():
    global ADMIN_ID
    if ADMIN_ID:
        return ADMIN_ID
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT val FROM config WHERE key='admin_id'")
        row = c.fetchone()
        conn.close()
        if row:
            ADMIN_ID = row[0]
            return ADMIN_ID
    except Exception:
        pass
    return None

def set_admin_id(uid):
    global ADMIN_ID
    ADMIN_ID = uid
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO config VALUES ('admin_id', ?)", (uid,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_warn_count(chat_id, user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0

def add_warn(chat_id, user_id):
    try:
        curr = get_warn_count(chat_id, user_id) + 1
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO warns VALUES (?, ?, ?)", (chat_id, user_id, curr))
        conn.commit()
        conn.close()
        return curr
    except Exception:
        return 1

def reset_user_warns(chat_id, user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

def save_filter(chat_id, keyword, reply):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO filters VALUES (?, ?, ?)", (chat_id, keyword.lower(), reply))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_filters(chat_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT keyword, reply FROM filters WHERE chat_id=?", (chat_id,))
        rows = c.fetchall()
        conn.close()
        return dict(rows)
    except Exception:
        return {}

def register_chat(chat_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO chats VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_all_chats():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_id FROM chats")
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []

# ==================== HELPERS ====================
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(REQ_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Force-sub safe bypass: {e}", flush=True)
        return True

def get_join_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_chan = types.InlineKeyboardButton("📢 ১. অফিশিয়াল চ্যানেলে জয়েন করুন (@rafimhossen3)", url=REQ_CHANNEL_LINK)
    btn_check = types.InlineKeyboardButton("✅ জয়েন সম্পন্ন করেছি (Verify)", callback_data="check_sub")
    markup.add(btn_chan, btn_check)
    return markup

def is_group_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

def get_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🔄 রিস্টার্ট করুন"))
    markup.add(types.KeyboardButton("📖 কমান্ড লিস্ট"), types.KeyboardButton("👤 আমার আইডি ও তথ্য"))
    markup.add(types.KeyboardButton("🛡️ অ্যাডমিনগণ"), types.KeyboardButton("📜 গ্রুপের নিয়ম"))
    markup.add(types.KeyboardButton("➕ গ্রুপে যুক্ত করুন"), types.KeyboardButton("📢 চ্যানেলে যুক্ত করুন"))
    return markup

MODULE_DETAILS = {
    "admin": (
        "🛡️ **Admin Module (অ্যাডমিন ম্যানেজমেন্ট):**\n\n"
        "গ্রুপের প্রশাসক ও অ্যাডমিনদের পরিচালনা করার মডিউল।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/admins` - গ্রুপের বর্তমান অ্যাডমিন তালিকা দেখুন।\n"
        "• `/promote` - কোনো মেম্বারকে অ্যাডমিন বানান।\n"
        "• `/demote` - কাউকে অ্যাডমিন পদ থেকে সরান।\n"
        "• `/admincache` - বটের মেমোরি রিফ্রেশ করুন।"
    ),
    "antiflood": (
        "🌊 **Antiflood (ফ্লাড প্রোটেকশন):**\n\n"
        "একটানা দ্রুত মেসেজ পাঠিয়ে গ্রুপে স্প্যামিং বন্ধ করার সিস্টেম।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/flood` - বর্তমান সেটিংস দেখুন।\n"
        "• `/setflood <সংখ্যা>` - কত মেসেজ পাঠালে মিউট হবে তা সেট করুন (যেমন: `/setflood 5`)।\n"
        "• `/setfloodmode <mute/ban>` - ফ্লাডের শাস্তি নির্ধারণ করুন।"
    ),
    "antiraid": (
        "⚔️ **AntiRaid (রেইড অ্যাটাক প্রোটেকশন):**\n\n"
        "হঠাৎ একসাথে শত শত ফেক মেম্বার বা স্প্যামার বট হামলা চালালে অটোমেটিক গ্রুপ লক করে দেওয়া।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/antiraid <on/off>` - রেইড প্রটেকশন অন বা অফ করুন।"
    ),
    "approval": (
        "🤝 **Approval (মেম্বার অ্যাপ্রুভাল):**\n\n"
        "নির্দিষ্ট বিশ্বস্ত মেম্বারদের অনুমোদন দিন যাতে কোনো রেস্ট্রিকশন তাদের ওপর প্রযোজ্য না হয়।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/approve` - মেসেজে রিপ্লাই দিয়ে মেম্বারকে অ্যাপ্রুভ করুন।\n"
        "• `/unapprove` - অনুমোদন তুলে নিন।\n"
        "• `/approved` - অনুমোদিত মেম্বারদের তালিকা।"
    ),
    "bans": (
        "🚫 **Bans (ব্যান ও বহিষ্কার):**\n\n"
        "গ্রুপের খারাপ সদস্যদের গ্রুপ থেকে বের করে দেওয়া।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/ban` - মেম্বারকে চিরতরে ব্যান করুন।\n"
        "• `/tban <সময়>` - নির্দিষ্ট সময়ের জন্য ব্যান করুন (যেমন: `/tban 2d`)।\n"
        "• `/unban` - ব্যান তুলে নিন।\n"
        "• `/kick` - গ্রুপ থেকে সাময়িক বের করে দিন।"
    ),
    "blocklists": (
        "⛔ **Blocklists (নিষিদ্ধ শব্দ তালিকা):**\n\n"
        "গ্রুপে নির্দিষ্ট কোনো গালি বা খারাপ টেক্সট স্বয়ংক্রিয়ভাবে মুছে ফেলার সুবিধা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/blocklist` - নিষিদ্ধ শব্দসমূহের তালিকা।\n"
        "• `/addblocklist <শব্দ>` - শব্দ নিষিদ্ধ করুন।\n"
        "• `/unblocklist <শব্দ>` - নিষিদ্ধ তালিকা থেকে শব্দ মুছুন।"
    ),
    "captcha": (
        "🤖 **CAPTCHA (হিউম্যান ভেরিফিকেশন):**\n\n"
        "নতুন মেম্বার জয়েন করলে সে রোবট না মানুষ তা ভেরিফাই করার জন্য ক্যাপচা বাটন দেখায়। চাপ না দিলে মিউট থাকে।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/captcha <on/off>` - ক্যাপচা চালু বা বন্ধ করুন।"
    ),
    "cleancomma": (
        "🧹 **Clean Commands (কমান্ড ক্লিনার):**\n\n"
        "মেম্বারদের দেওয়া `/` বা `!` কমান্ডের মেসেজ স্বয়ংক্রিয়ভাবে মুছে চ্যাট ফ্রেশ রাখা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/cleancommand <on/off>` - কমান্ড ডিলিট চালু/বন্ধ করুন।"
    ),
    "cleanservice": (
        "🧽 **Clean Service (সার্ভিস মেসেজ ক্লিনার):**\n\n"
        "গ্রুপে 'অমুক জয়েন করেছে' বা 'গ্রুপ ত্যাগ করেছে' এই বিরক্তিকর মেসেজগুলো স্বয়ংক্রিয়ভাবে ডিলিট করে।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/cleanservice <on/off>` - সার্ভিস মেসেজ ডিলিট চালু করুন।"
    ),
    "connections": (
        "🔗 **Connections (রিমোট কানেক্ট):**\n\n"
        "বটের ইনবক্স থেকেই যেকোনো গ্রুপ নিয়ন্ত্রণ করার সুবিধা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/connect <গ্রুপ আইডি>` - ইনবক্সের সাথে গ্রুপ কানেক্ট করুন।\n"
        "• `/disconnect` - সংযোগ বিচ্ছিন্ন করুন।"
    ),
    "disabling": (
        "📴 **Disabling (কমান্ড নিয়ন্ত্রণ):**\n\n"
        "গ্রুপের সাধারণ মেম্বারদের জন্য নির্দিষ্ট কমান্ডগুলো নিষ্ক্রিয় করে রাখা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/disable <কমান্ড>` - কমান্ড বন্ধ করুন।\n"
        "• `/enable <কমান্ড>` - আবার চালু করুন।"
    ),
    "federations": (
        "🌐 **Federations (ফেডারেশন নেটওয়ার্ক):**\n\n"
        "অনেকগুলো গ্রুপ একসাথে যুক্ত করে এক ক্লিকে সব গ্রুপ থেকে ব্যান করার নেটওয়ার্ক।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/fban` - এক ক্লিকে ফেডারেশনের সব গ্রুপ থেকে ব্যান করুন।"
    ),
    "filters": (
        "🎯 **Filters (অটো রিপ্লাই):**\n\n"
        "নির্দিষ্ট শব্দ লিখলে বট থেকে স্বয়ংক্রিয় উত্তর পাওয়ার ব্যবস্থা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/addfilter <শব্দ> | <উত্তর>` - নতুন ফিল্টার যুক্ত করুন।\n"
        "• `/filters` - সক্রিয় ফিল্টারের তালিকা।\n"
        "• `/stop <শব্দ>` - ফিল্টার মুছে দিন।"
    ),
    "formatting": (
        "✍️ **Formatting (টেক্সট স্টাইল):**\n\n"
        "মেসেজ সুন্দর করে সাজানোর নিয়ম:\n\n"
        "• `*বোল্ড*` - লেখা মোটা হবে।\n"
        "• `_ইটালিক_` - লেখা বাঁকা হবে।\n"
        "• `[লেখা](লিঙ্ক)` - লেখার ভেতর লিঙ্ক।"
    ),
    "greetings": (
        "👋 **Greetings (স্বাগতম বার্তা):**\n\n"
        "নতুন সদস্য প্রবেশ করলে সুন্দর স্বাগতম বার্তা জানানো।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/welcome <on/off>` - ওয়েলকাম মেসেজ চালু/বন্ধ।\n"
        "• `/setwelcome <বার্তা>` - কাস্টম ওয়েলকাম সেট করুন।"
    ),
    "importexport": (
        "📦 **Import/Export (ব্যাকআপ ও রিস্টোর):**\n\n"
        "গ্রুপের সকল ফিল্টার ও সেটিংস ব্যাকআপ ফাইল হিসেবে সেভ করা বা আপলোড করা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/export` - ব্যাকআপ ফাইল ডাউনলোড করুন।\n"
        "• `/import` - ফাইল দিয়ে রিস্টোর করুন।"
    ),
    "languages": (
        "🌍 **Languages (ভাষা পরিবর্তন):**\n\n"
        "বটের ভাষা পরিবর্তন করার কমান্ড।\n\n"
        "• `/setlang` - ভাষা নির্বাচন করুন।"
    ),
    "locks": (
        "🔒 **Locks (কনটেন্ট লক):**\n\n"
        "গ্রুপে লিঙ্ক, ফটো, ভিডিও, স্টিকার ইত্যাদি পাঠানো বন্ধ রাখা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/lock links` - গ্রুপের লিঙ্ক শেয়ার বন্ধ করুন।\n"
        "• `/lock photo` - ফটো পাঠানো বন্ধ করুন।\n"
        "• `/unlock <নাম>` - আনলক করুন।"
    ),
    "logchannels": (
        "📝 **Log Channels (লগ চ্যানেল):**\n\n"
        "গ্রুপে কে কাকে ব্যান করল বা কি ডিলিট হলো তা আলাদা চ্যানেলে রেকর্ড রাখা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/setlog` - লগ চ্যানেল সেট করুন।"
    ),
    "misc": (
        "⚙️ **Misc (বিবিধ টুলস):**\n\n"
        "প্রয়োজনীয় সাধারণ টুলস।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/id` - আপনার টেলিগ্রাম আইডি দেখুন।\n"
        "• `/info` - ইউজারের প্রোফাইল ডাটা দেখুন।"
    ),
    "notes": (
        "📌 **Notes (নোট সেভ):**\n\n"
        "জরুরি কোনো তথ্য সেভ করে রাখা যা হ্যাশট্যাগ দিয়ে মেম্বাররা দেখতে পাবে।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/save <নাম> <মেসেজ>` - নোট সেভ করুন।\n"
        "• `/notes` - সব সেভ করা নোট।"
    ),
    "pin": (
        "📍 **Pin (মেসেজ পিন):**\n\n"
        "গুরুত্বপূর্ণ মেসেজ গ্রুপের শীর্ষে পিন করা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/pin` - মেসেজে রিপ্লাই দিয়ে পিন করুন।\n"
        "• `/unpin` - আনপিন করুন।"
    ),
    "privacy": (
        "🔐 **Privacy (নিরাপত্তা):**\n\n"
        "গ্রুপ মেম্বারদের গোপনীয়তা রক্ষা ও নিরাপত্তা সংক্রান্ত মডিউল।"
    ),
    "purges": (
        "🗑️ **Purges (ম্যাসিভ মেসেজ ডিলিট):**\n\n"
        "এক ক্লিকে অনেক মেসেজ ডিলিট করার ব্যবস্থা।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/purge` - যেখান থেকে মুছবেন সেখানে রিপ্লাই করে কমান্ড দিন।"
    ),
    "reports": (
        "📢 **Reports (মেম্বার রিপোর্ট):**\n\n"
        "গ্রুপে সমস্যা হলে এডমিনদের ডাকা।\n\n"
        "• মেসেজে রিপ্লাই দিয়ে `@admin` বা `/report` লিখলে সব অ্যাডমিনের কাছে অ্যালার্ট যাবে।"
    ),
    "rules": (
        "📜 **Rules (গ্রুপের কানুন):**\n\n"
        "গ্রুপের নিয়মাবলী সেট ও পড়ার সিস্টেম।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/rules` - নিয়ম দেখুন।\n"
        "• `/setrules <নিয়ম>` - নিয়ম সেট করুন।"
    ),
    "topics": (
        "💬 **Topics (টপিকস ও ফোরাম):**\n\n"
        "টেলিগ্রাম ফোরাম গ্রুপের সাব-টপিক ম্যানেজমেন্ট।"
    ),
    "warnings": (
        "⚠️ **Warnings (ওয়ার্নিং সিস্টেম):**\n\n"
        "নিয়ম না মানলে সতর্কবার্তা দেওয়া। ৩টি পূর্ণ হলে অটো মিউট/ব্যান।\n\n"
        "**প্রয়োজনীয় কমান্ডসমূহ:**\n"
        "• `/warn` - মেম্বারের মেসেজে রিপ্লাই দিয়ে ওয়ার্ন দিন।\n"
        "• `/warns` - কত ওয়ার্ন পেয়েছে দেখুন।"
    ),
    "custominstances": (
        "⭐ **Custom Instances:**\n\n"
        "সম্পূর্ণ নিজস্ব ব্র্যান্ডে এবং প্রোফাইল ছবিতে ক্লোন বট বানানোর সুবিধা।\n\n"
        "• যোগাযোগের ঠিকানা: @rafimhossen"
    )
}

MODULE_LIST = [
    ("🛡️ Admin", "admin"), ("🌊 Antiflood", "antiflood"), ("⚔️ AntiRaid", "antiraid"),
    ("🤝 Approval", "approval"), ("🚫 Bans", "bans"), ("⛔ Blocklists", "blocklists"),
    ("🤖 CAPTCHA", "captcha"), ("🧹 Clean Comma", "cleancomma"), ("🧽 Clean Service", "cleanservice"),
    ("🔗 Connect", "connections"), ("📴 Disabling", "disabling"), ("🌐 Federation", "federations"),
    ("🎯 Filters", "filters"), ("✍️ Formatting", "formatting"), ("👋 Greetings", "greetings"),
    ("📦 Backup", "importexport"), ("🌍 Language", "languages"), ("🔒 Locks", "locks"),
    ("📝 Logs", "logchannels"), ("⚙️ Misc", "misc"), ("📌 Notes", "notes"),
    ("📍 Pin", "pin"), ("🔐 Privacy", "privacy"), ("🗑️ Purges", "purges"),
    ("📢 Reports", "reports"), ("📜 Rules", "rules"), ("💬 Topics", "topics")
]

def get_rose_help_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(name, callback_data=f"helpmod_{key}") for name, key in MODULE_LIST]
    markup.add(*btns)
    markup.row(
        types.InlineKeyboardButton("⚠️ Warnings", callback_data="helpmod_warnings"),
        types.InlineKeyboardButton("⭐ Custom Instances", callback_data="helpmod_custominstances")
    )
    markup.row(types.InlineKeyboardButton("👨‍💻 Developer Support (@rafimhossen)", url="https://t.me/rafimhossen"))
    return markup

# ==================== HANDLERS ====================
# বট গ্রুপে অ্যাড হওয়ার ট্র্যাকিং হ্যান্ডলার
@bot.my_chat_member_handler()
def handle_bot_add_to_group(message: types.ChatMemberUpdated):
    new_status = message.new_chat_member.status
    old_status = message.old_chat_member.status
    
    if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator']:
        group = message.chat
        added_by = message.from_user
        register_chat(group.id)
        
        target_admin = get_admin_id()
        if target_admin:
            admin_alert = (
                f"📢 <b>Bot Added to a New Group!</b>\n\n"
                f"<b>Group Name:</b> {group.title}\n"
                f"<b>Group ID:</b> <code>{group.id}</code>\n"
                f"<b>Group Username:</b> @{group.username if group.username else 'Private Group'}\n"
                f"<b>Added By:</b> {added_by.first_name} {added_by.last_name or ''}\n"
                f"<b>User ID:</b> <code>{added_by.id}</code>\n"
                f"<b>Username:</b> @{added_by.username if added_by.username else 'None'}"
            )
            try:
                bot.send_message(target_admin, admin_alert, parse_mode="HTML")
            except Exception as e:
                print(f"Failed to notify admin: {e}", flush=True)

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_member(message):
    register_chat(message.chat.id)
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:
            continue
        try:
            bot.restrict_chat_member(message.chat.id, member.id, permissions=types.ChatPermissions(can_send_messages=False))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ আমি নিয়ম মেনে চলব (Verify)", callback_data=f"verify_rule_{member.id}"))
            bot.send_message(
                message.chat.id,
                f"👋 স্বাগতম [{member.first_name}](tg://user?id={member.id})!\n\n"
                f"🛡️ **গ্রুপে কথা বলতে নিচের বাটনে চাপ দিয়ে নিয়ম স্বীকার করুন:**",
                reply_markup=markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Mute error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_rule_"))
def handle_verify_rules(call):
    target_id = int(call.data.split("_")[2])
    if call.from_user.id != target_id:
        bot.answer_callback_query(call.id, "❌ এই বাটনটি নতুন মেম্বারের জন্য!", show_alert=True)
        return
    try:
        bot.restrict_chat_member(
            call.message.chat.id,
            target_id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল হয়েছে!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if message.from_user.username != "rafimhossen":
        bot.reply_to(message, "❌ এটি কেবল বটের ওনারের জন্য সংরক্ষিত!")
        return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "⚠️ ব্যবহার: /broadcast আপনার মেসেজ")
        return

    chats = get_all_chats()
    sent_count = 0
    bot.reply_to(message, f"📢 মোট {len(chats)} টি চ্যাটে ব্রডকাস্ট শুরু হচ্ছে...")
    for cid in chats:
        try:
            bot.send_message(cid, f"📢 অফিসিয়াল অ্যানাউন্সমেন্ট:\n\n{text}")
            sent_count += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Broadcast failed for {cid}: {e}", flush=True)
    bot.send_message(message.chat.id, f"✅ সফলভাবে {sent_count} টি চ্যাটে পাঠানো হয়েছে।")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_subscription(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ আপনার ভেরিফিকেশন সফল হয়েছে।", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message, call.from_user)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো @rafimhossen3 চ্যানেলে জয়েন করেননি!", show_alert=True)

@bot.callback_query_handler(func=lambda call: True)
def handle_universal_callbacks(call):
    if call.data in ["check_sub"] or call.data.startswith("verify_rule_") or call.data.startswith("prov_"):
        return

    if not is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ আগে আমাদের চ্যানেলে জয়েন থাকতে হবে!", show_alert=True)
        bot.send_message(
            call.message.chat.id,
            "⚠️ **বট ব্যবহার করতে হলে অবশ্যই আমাদের অফিসিয়াল চ্যানেলে যুক্ত হতে হবে!**\n\nনিচের লিংকে জয়েন করে ভেরিফাই করুন:",
            reply_markup=get_join_markup(),
            parse_mode='Markdown'
        )
        return

    if call.data in ["back_to_menu", "back_menu"]:
        bot.edit_message_text(
            "⚡ **মডিউল ড্যাশবোর্ড:**\nনিচের যেকোনো মডিউলে ক্লিক করে সেটির কাজ এবং প্রয়োজনীয় কমান্ডগুলো দেখে নিন:\n\nAll commands can be used with: `/` `!`",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_rose_help_menu()
        )
        return

    raw_key = call.data.replace("helpmod_", "").replace("mod_", "").replace("info_", "").replace("desc_", "").strip().lower()
    detail_msg = MODULE_DETAILS.get(raw_key)

    if not detail_msg:
        for k, v in MODULE_DETAILS.items():
            if k in raw_key:
                detail_msg = v
                break

    if not detail_msg:
        detail_msg = f"📌 **{raw_key.capitalize()} Module:**\nএই মডিউলটি আপনার গ্রুপে সক্রিয় রয়েছে। কমান্ড জানতে ইনবক্সে `/help` ব্যবহার করুন।"

    nav_markup = types.InlineKeyboardMarkup()
    nav_markup.row(
        types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu"),
        types.InlineKeyboardButton("👨‍💻 Support Admin", url="https://t.me/rafimhossen")
    )
    
    try:
        bot.edit_message_text(
            detail_msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=nav_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Edit msg error: {e}")

def send_welcome(message, user=None):
    u = user if user else message.from_user
    text = (
        f"🌹 **স্বাগতম, {u.first_name}!** 👋\n\n"
        "আমি আপনার অ্যাডভান্সড গ্রুপ ম্যানেজমেন্ট ও অটোমেশন রোবট — **Rafim Rose Manager**।\n\n"
        "🛡️ গ্রুপকে লিঙ্ক-স্প্যামারদের হাত থেকে রক্ষা করতে এবং স্মুথলি কন্ট্রোল করতে আমাকে আপনার গ্রুপে **Admin** হিসেবে যুক্ত করুন।"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_reply_keyboard(), parse_mode='Markdown')
    bot.send_message(
        message.chat.id, 
        "⚡ **মডিউল ড্যাশবোর্ড:**\nনিচের যেকোনো মডিউলে ক্লিক করে সেটির কাজ এবং প্রয়োজনীয় কমান্ডগুলো দেখে নিন:\n\nAll commands can be used with: `/` `!`", 
        reply_markup=get_rose_help_menu()
    )

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    try:
        register_chat(message.chat.id)
        if message.chat.type == 'private':
            user = message.from_user
            
            # অ্যাডমিন আইডি শনাক্তকরণ ও কনফিগারেশন
            if user.username and user.username.lower() == ADMIN_USERNAME.lower():
                set_admin_id(user.id)
                bot.reply_to(message, f"👑 স্বাগতম অ্যাডমিন @{ADMIN_USERNAME}! আপনার আইডি (`{user.id}`) কনফিগার হয়েছে। সকল অ্যালার্ট ও তথ্য এখানে পাঠানো হবে।", parse_mode='Markdown')
                send_welcome(message)
                return

            # ইউজার ওপেন করার অ্যালার্ট সরাসরি অ্যাডমিনের কাছে পাঠানো
            target_admin = get_admin_id()
            if target_admin:
                admin_alert = (
                    f"👤 <b>New User Started Bot!</b>\n\n"
                    f"<b>Name:</b> {user.first_name} {user.last_name or ''}\n"
                    f"<b>Username:</b> @{user.username if user.username else 'None'}\n"
                    f"<b>User ID:</b> <code>{user.id}</code>\n"
                    f"<b>Language:</b> {user.language_code or 'Unknown'}"
                )
                try:
                    bot.send_message(target_admin, admin_alert, parse_mode="HTML")
                except Exception as e:
                    print(f"Failed to notify admin: {e}", flush=True)

            # চ্যানেল/গ্রুপ জয়েন ভেরিফিকেশন চেক
            if not is_subscribed(message.from_user.id):
                bot.send_message(
                    message.chat.id,
                    "⚠️ **বটটি ব্যবহার করার জন্য আপনাকে আমাদের অফিসিয়াল চ্যানেলে জয়েন থাকতে হবে!**\n\nনিচের বাটনে চাপ দিয়ে জয়েন করে **Verify** করুন:",
                    reply_markup=get_join_markup(),
                    parse_mode='Markdown'
                )
                return
            send_welcome(message)
        else:
            bot.reply_to(message, "✅ বট সক্রিয় রয়েছে! সমস্ত কমান্ড দেখতে ইনবক্সে /help লিখুন।")
    except Exception as e:
        print(f"Error in start: {e}", flush=True)

@bot.message_handler(func=lambda msg: msg.text in [
    "🔄 রিস্টার্ট করুন", "📖 কমান্ড লিস্ট", "👤 আমার আইডি ও তথ্য", "🛡️ অ্যাডমিনগণ", "📜 গ্রুপের নিয়ম", "➕ গ্রুপে যুক্ত করুন", "📢 চ্যানেলে যুক্ত করুন"
])
def reply_buttons_handler(message):
    try:
        register_chat(message.chat.id)
        if message.chat.type == 'private' and not is_subscribed(message.from_user.id):
            bot.send_message(message.chat.id, "⚠️ অনুগ্রহ করে আগে আমাদের চ্যানেলে জয়েন করুন!", reply_markup=get_join_markup())
            return
            
        bot_info = bot.get_me()
        if message.text == "🔄 রিস্টার্ট করুন":
            send_welcome(message)
        elif message.text == "📖 কমান্ড লিস্ট":
            bot.send_message(message.chat.id, "নিচের মডিউলগুলোতে চাপ দিয়ে বিস্তারিত কমান্ড জেনে নিন:", reply_markup=get_rose_help_menu())
        elif message.text == "👤 আমার আইডি ও তথ্য":
            user = message.from_user
            info = (
                f"👤 **আপনার প্রোফাইল তথ্য:**\n"
                f"• নাম: {user.first_name}\n"
                f"• ইউজারনেম: @{user.username or 'নাই'}\n"
                f"• টেলিগ্রাম আইডি: `{user.id}`"
            )
            bot.send_message(message.chat.id, info, parse_mode='Markdown')
        elif message.text == "🛡️ অ্যাডমিনগণ":
            bot.send_message(message.chat.id, "গ্রুপে গিয়ে `/admins` কমান্ড দিলে অ্যাডমিনদের লিস্ট দেখতে পাবেন।")
        elif message.text == "📜 গ্রুপের নিয়ম":
            bot.send_message(message.chat.id, "📜 গ্রুপে কোনো লিঙ্ক শেয়ার, বিজ্ঞাপন ও স্প্যামিং করা সম্পূর্ণ নিষিদ্ধ।")
        elif message.text == "➕ গ্রুপে যুক্ত করুন":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("➕ Add Bot to Group", url=f"https://t.me/{bot_info.username}?startgroup=true"))
            bot.send_message(message.chat.id, "আপনার গ্রুপে বটটি যুক্ত করতে নিচের বাটনে চাপ দিন:", reply_markup=markup)
        elif message.text == "📢 চ্যানেলে যুক্ত করুন":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📢 Add Bot to Channel", url=f"https://t.me/{bot_info.username}?startchannel=true"))
            bot.send_message(message.chat.id, "চ্যানেলে যুক্ত করতে নিচের বাটনে চাপ দিন:", reply_markup=markup)
    except Exception as e:
        print(f"Error in reply buttons: {e}", flush=True)

@bot.message_handler(commands=['pin', 'warn', 'ban', 'purge', 'kick', 'mute'])
def handle_admin_commands(message):
    if message.chat.type == 'private':
        return
    register_chat(message.chat.id)
    is_anon = message.sender_chat and message.sender_chat.id == message.chat.id
    is_user_admin = is_anon or (message.from_user and is_group_admin(message.chat.id, message.from_user.id))

    if not is_user_admin:
        bot.reply_to(message, "❌ এই কমান্ডটি শুধুমাত্র গ্রুপের অ্যাডমিনগণ ব্যবহার করতে পারবেন!")
        return

    text_clean = message.text.split()[0].split('@')[0].replace('/', '')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Click to prove admin", callback_data=f"prov_{text_clean}_{message.message_id}"))
    
    bot.reply_to(
        message, 
        "It looks like you're anonymous.\nTap this button to confirm your identity.", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("prov_"))
def verify_and_execute_admin(call):
    data_parts = call.data.split("_")
    cmd = data_parts[1]
    
    if not is_group_admin(call.message.chat.id, call.from_user.id):
        bot.answer_callback_query(call.id, "❌ আপনি এই গ্রুপের অ্যাডমিন নন!", show_alert=True)
        return

    bot.answer_callback_query(call.id, "✅ অ্যাডমিন ভেরিফাই হয়েছে!")
    
    try:
        orig_msg = call.message.reply_to_message
        chat_id = call.message.chat.id

        if cmd == 'pin':
            if orig_msg:
                bot.pin_chat_message(chat_id, orig_msg.message_id)
                bot.edit_message_text("📌 মেসেজটি সফলভাবে পিন করা হয়েছে!", chat_id, call.message.message_id)
            else:
                bot.edit_message_text("⚠️ পিন করার জন্য মেসেজে রিপ্লাই দিন।", chat_id, call.message.message_id)

        elif cmd == 'warn':
            if orig_msg and orig_msg.from_user:
                target = orig_msg.from_user
                curr = add_warn(chat_id, target.id)
                if curr >= 3:
                    bot.restrict_chat_member(chat_id, target.id, permissions=types.ChatPermissions(can_send_messages=False))
                    bot.edit_message_text(f"🚫 [{target.first_name}](tg://user?id={target.id}) ৩ বার সতর্ক পেয়ে মিউট হয়েছেন!", chat_id, call.message.message_id, parse_mode='Markdown')
                    reset_user_warns(chat_id, target.id)
                else:
                    bot.edit_message_text(f"⚠️ [{target.first_name}](tg://user?id={target.id}) সতর্কবার্তা: **{curr}/3** (ডাটাবেজে সংরক্ষিত)", chat_id, call.message.message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text("⚠️ সতর্ক করতে ইউজারের মেসেজে রিপ্লাই দিন।", chat_id, call.message.message_id)

        elif cmd == 'ban':
            if orig_msg and orig_msg.from_user:
                bot.ban_chat_member(chat_id, orig_msg.from_user.id)
                bot.edit_message_text("🚫 সদস্যকে গ্রুপ থেকে স্থায়ীভাবে ব্যান করা হয়েছে।", chat_id, call.message.message_id)
            else:
                bot.edit_message_text("⚠️ ব্যান করতে ইউজারের মেসেজে রিপ্লাই দিন।", chat_id, call.message.message_id)

        elif cmd == 'purge':
            if orig_msg:
                start_id = orig_msg.message_id
                end_id = call.message.message_id
                for mid in range(start_id, end_id + 1):
                    try:
                        bot.delete_message(chat_id, mid)
                    except Exception:
                        pass
            else:
                bot.edit_message_text("⚠️ যেখান থেকে মুছবেন সেখানে রিপ্লাই দিন।", chat_id, call.message.message_id)

    except Exception as e:
        bot.answer_callback_query(call.id, f"ত্রুটি: {e}", show_alert=True)

@bot.message_handler(commands=['addfilter'])
def add_filter_cmd(message):
    if message.chat.type == 'private' or not is_group_admin(message.chat.id, message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট: `/addfilter শব্দ | উত্তর`", parse_mode='Markdown')
        return
    content = parts[1].split('|')
    if len(content) < 2:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট: `/addfilter শব্দ | উত্তর`", parse_mode='Markdown')
        return
    kw = content[0].strip().lower()
    ans = content[1].strip()
    save_filter(message.chat.id, kw, ans)
    bot.reply_to(message, f"🎯 ফিল্টার সেভ হয়েছে: `{kw}`", parse_mode='Markdown')

@bot.message_handler(commands=['filters'])
def list_filters(message):
    if message.chat.type == 'private':
        return
    filters = get_filters(message.chat.id)
    if not filters:
        bot.reply_to(message, "📂 এই গ্রুপে কোনো কাস্টম ফিল্টার নেই।")
        return
    txt = "📋 **গ্রুপের ফিল্টার তালিকা:**\n\n"
    for kw in filters.keys():
        txt += f"• `{kw}`\n"
    bot.reply_to(message, txt, parse_mode='Markdown')

@bot.message_handler(commands=['rules'])
def send_rules(message):
    bot.reply_to(message, "📜 **গ্রুপের নিয়মাবলী:**\n\n১. গ্রুপে লিঙ্ক শেয়ার বা স্প্যামিং সম্পূর্ণ নিষেধ।\n২. গ্রুপের পরিচ্ছন্নতা বজায় রাখুন।")

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def group_filters_and_links(message):
    if not message.text:
        return
    register_chat(message.chat.id)
    is_admin = is_group_admin(message.chat.id, message.from_user.id) if message.from_user else False
    
    if re.search(r'(https?://[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+)', message.text):
        if not is_admin:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"⚠️ [{message.from_user.first_name}](tg://user?id={message.from_user.id}), লিঙ্ক শেয়ার সম্পূর্ণ নিষিদ্ধ!", parse_mode='Markdown')
            except Exception:
                pass
            return

    chat_filters = get_filters(message.chat.id)
    text_lower = message.text.lower()
    for kw, resp in chat_filters.items():
        if kw in text_lower:
            bot.reply_to(message, resp)
            break

# ==================== CRASH-PROOF BOT RUNNER ====================
if __name__ == '__main__':
    keep_alive()
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"Webhook clean error: {e}", flush=True)

    bot_user = bot.get_me()
    print(f"Logged in as @{bot_user.username}. Ready for actions!", flush=True)
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Critical connection drop recovered: {e}", flush=True)
            time.sleep(3)
