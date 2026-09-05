import os
import sys
import random
import re
import time
import telebot
from telebot import types
from keep_alive import keep_alive

print("--- Starting Rafim Rose Manager Bot ---", flush=True)

BOT_TOKEN = "8886219226:AAHAk9py2IIsXQZKF3X6CwyKWswQalJpZdM"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

# চ্যানেল মেম্বারশিপ কনফিগারেশন
REQ_CHANNEL = "@rafimhossen3"
REQ_CHANNEL_LINK = "https://t.me/rafimhossen3"

USER_WARNS = {}
GROUP_FILTERS = {}

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(REQ_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Force-sub bypass (bot might not be admin in channel): {e}", flush=True)
        # চ্যানেল সংক্রান্ত কারণে যাতে বট হ্যাং না হয়ে যায়
        return True

def get_join_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_chan = types.InlineKeyboardButton("📢 ১. অফিশিয়াল চ্যানেলে জয়েন করুন (@rafimhossen3)", url=REQ_CHANNEL_LINK)
    btn_check = types.InlineKeyboardButton("✅ জয়েন করেছি (Verify)", callback_data="check_sub")
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

# প্রতিটি বাটনের ফুল ডিটেইলস ও কমান্ড টিউটোরিয়াল
MODULE_DETAILS = {
    "admin": (
        "🛡️ **Admin (অ্যাডমিন ম্যানেজমেন্ট):**\n\n"
        "গ্রুপের প্রশাসক বা অ্যাডমিনদের সহজে পরিচালনা করার জন্য এই মডিউলটি ব্যবহার করা হয়।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/admins` - গ্রুপের বর্তমান অ্যাডমিন তালিকা দেখুন।\n"
        "• `/promote` - কোনো মেম্বারকে অ্যাডমিন পদে উন্নীত করুন।\n"
        "• `/demote` - কাউকে অ্যাডমিন পদ থেকে সাধারণ মেম্বারে নামান।\n"
        "• `/admincache` - নতুন অ্যাডমিন যুক্ত হলে বটের ডাটা রিফ্রেশ করুন।"
    ),
    "antiflood": (
        "🌊 **Antiflood (স্প্যাম ফ্লাড প্রোটেকশন):**\n\n"
        "একটানা দ্রুত মেসেজ পাঠিয়ে গ্রুপে বিশৃঙ্খলা সৃষ্টি করা প্রতিহত করতে এটি সক্রিয় থাকে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/flood` - বর্তমান ফ্লাড সেটিংস ও সীমা দেখুন।\n"
        "• `/setflood <সংখ্যা>` - নির্দিষ্ট কতগুলো মেসেজ একনাগাড়ে দিলে সতর্ক বা মিউট হবে তা নির্ধারণ করুন (যেমন: `/setflood 5`)।\n"
        "• `/setfloodmode <mute/ban>` - ফ্লাড সীমা ভাঙলে কী শাস্তি দেওয়া হবে তা সেট করুন।"
    ),
    "antiraid": (
        "⚔️ **AntiRaid (রেইড ও বট অ্যাটাক প্রোটেকশন):**\n\n"
        "গ্রুপে হঠাৎ একসাথে শত শত ফেক আইডি বা স্প্যামার বটের অনুপ্রবেশ ঠেকাতে এটি কার্যকর।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/antiraid <on/off>` - রেইড প্রোটেকশন চালু বা বন্ধ করুন।\n"
        "• `/raidtime <সময়>` - কোনো আক্রমণ হলে গ্রুপ কত সময় লক থাকবে তা সেট করুন।"
    ),
    "approval": (
        "🤝 **Approval (মেম্বার অ্যাপ্রুভাল):**\n\n"
        "নির্দিষ্ট কিছু বিশ্বস্ত মেম্বারকে অনুমোদন দেওয়া, যাতে অ্যান্টি-স্প্যাম সিস্টেম তাদের মেসেজ বা লিঙ্ক ডিলিট না করে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/approve` - মেসেজে রিপ্লাই দিয়ে মেম্বারকে নিরাপদ হিসেবে অ্যাপ্রুভ করুন।\n"
        "• `/unapprove` - মেম্বারের অনুমোদন বাতিল করুন।\n"
        "• `/approved` - অনুমোদিত সব মেম্বারদের তালিকা দেখুন।"
    ),
    "bans": (
        "🚫 **Bans (ব্যান ও বহিষ্কার):**\n\n"
        "স্প্যামার ও বিশৃঙ্খলা সৃষ্টিকারীদের গ্রুপ থেকে স্থায়ীভাবে বহিষ্কারের ব্যবস্থা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/ban` - মেম্বারকে গ্রুপ থেকে চিরতরে ব্যান করুন।\n"
        "• `/tban <সময়>` - সাময়িক সময়ের জন্য ব্যান করুন (যেমন: `/tban 2d` ২ দিনের জন্য)।\n"
        "• `/unban` - ব্যানের তালিকা থেকে কাউকে মুক্ত করুন।\n"
        "• `/kick` - মেম্বারকে গ্রুপ থেকে বের করে দেওয়া (পরে আবার জয়েন করতে পারবে)।"
    ),
    "blocklists": (
        "⛔ **Blocklists (নিষিদ্ধ শব্দ তালিকা):**\n\n"
        "কোনো গালি, আপত্তিকর শব্দ বা নির্দিষ্ট নিষিদ্ধ টেক্সট স্বয়ংক্রিয়ভাবে মুছে দেওয়ার সুবিধা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/blocklist` - নিষিদ্ধ শব্দসমূহের তালিকা দেখুন।\n"
        "• `/addblocklist <শব্দ>` - কোনো শব্দ নিষিদ্ধ করুন।\n"
        "• `/unblocklist <শব্দ>` - নিষিদ্ধ তালিকা থেকে শব্দ মুছুন।"
    ),
    "captcha": (
        "🤖 **CAPTCHA (হিউম্যান ভেরিফিকেশন):**\n\n"
        "নতুন কোনো মেম্বার গ্রুপে যুক্ত হলে সে রোবট নাকি মানুষ তা ভেরিফাই করার জন্য ক্যাপচা বাটন দেখায়।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/captcha <on/off>` - ক্যাপচা সিস্টেম চালু বা বন্ধ করুন।\n"
        "• `/captchamode <button/math>` - বাটনে ক্লিক নাকি সাধারণ গণিত সমাধান করে ভেরিফাই করবে তা সেট করুন।"
    ),
    "cleancomma": (
        "🧹 **Clean Commands (কমান্ড ক্লিনার):**\n\n"
        "মেম্বারদের দেওয়া `/` বা `!` দিয়ে শুরু হওয়া কমান্ড মেসেজগুলো কাজ শেষে চ্যাট থেকে স্বয়ংক্রিয়ভাবে মুছে চ্যাট ফ্রেশ রাখে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/cleancommand <on/off>` - কমান্ডের মেসেজ ক্লিন করা চালু বা বন্ধ করুন।"
    ),
    "cleanservice": (
        "🧽 **Clean Service (সার্ভিস মেসেজ ক্লিনার):**\n\n"
        "গ্রুপে 'অমুক জয়েন করেছে' বা 'অমুক গ্রুপ ত্যাগ করেছে' এই বিরক্তিকর মেসেজগুলো স্বয়ংক্রিয়ভাবে ডিলিট করে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/cleanservice <on/off>` - জয়েন/লিভ মেসেজ ডিলিট সিস্টেম চালু করুন।"
    ),
    "connections": (
        "🔗 **Connections (রিমোট গ্রুপ কানেক্ট):**\n\n"
        "বটের ইনবক্স (PM) থেকেই যেকোনো গ্রুপের সেটিংস দেখার ও পরিচালনা করার সিস্টেম।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/connect <গ্রুপ আইডি>` - ইনবক্সের সাথে গ্রুপ লিংক করুন।\n"
        "• `/disconnect` - সংযোগ বিচ্ছিন্ন করুন।"
    ),
    "disabling": (
        "📴 **Disabling (কমান্ড নিয়ন্ত্রণ):**\n\n"
        "গ্রুপের সাধারণ মেম্বারদের জন্য নির্দিষ্ট কিছু অপ্রয়োজনীয় কমান্ড নিষ্ক্রিয় করে রাখা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/disable <কমান্ডের নাম>` - নির্দিষ্ট কমান্ড বন্ধ করুন।\n"
        "• `/enable <কমান্ডের নাম>` - বন্ধ থাকা কমান্ড আবার চালু করুন।"
    ),
    "federations": (
        "🌐 **Federations (ফেডারেশন নেটওয়ার্ক):**\n\n"
        "একাধিক গ্রুপকে এক ছাতার নিচে এনে একটি বিশ্বস্ত নেটওয়ার্ক তৈরি করা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/fban` - একজন স্প্যামারকে ফেডারেশনের অধীনে থাকা সকল গ্রুপ থেকে এক ক্লিকেই ব্যান করুন।\n"
        "• `/unfban` - ফেডারেশন আনব্যান করুন।"
    ),
    "filters": (
        "🎯 **Filters (কাস্টম অটো-রিপ্লাই):**\n\n"
        "গ্রুপে মেম্বারদের নির্দিষ্ট প্রশ্নের জন্য বটের অটোমেটিক উত্তর সেট করার ফিচার।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/addfilter <শব্দ> | <উত্তর>` - নতুন ফিল্টার যুক্ত করুন।\n"
        "• `/filters` - আপনার গ্রুপের সমস্ত সক্রিয় ফিল্টারের তালিকা।\n"
        "• `/stop <শব্দ>` - কোনো ফিল্টার মুছে ফেলুন।"
    ),
    "formatting": (
        "✍️ **Formatting (টেক্সট ফরম্যাটিং স্টাইল):**\n\n"
        "বটের মাধ্যমে বোল্ড, ইটালিক, কোড ব্লক ও হাইপারলিংক দিয়ে মেসেজ সুন্দর করার নিয়ম:\n\n"
        "• `*বোল্ড টেক্সট*` -> মোটা লেখা।\n"
        "• `_ইটালিক টেক্সট_` -> বাঁকা লেখা।\n"
        "• `[টেক্সট](লিংক)` -> লেখার ভেতরে গোপন লিংক বসানো।"
    ),
    "greetings": (
        "👋 **Greetings (স্বাগতম ও বিদায় বার্তা):**\n\n"
        "নতুন সদস্য প্রবেশ করলে সুন্দর কাস্টম ওয়েলকাম মেসেজ পাঠানোর সিস্টেম।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/welcome <on/off>` - ওয়েলকাম মেসেজ চালু বা বন্ধ করুন।\n"
        "• `/setwelcome <বার্তা>` - আপনার গ্রুপের জন্য কাস্টম স্বাগতম বার্তা সেট করুন।"
    ),
    "importexport": (
        "📦 **Import/Export (গ্রুপ ব্যাকআপ ও রিস্টোর):**\n\n"
        "আপনার গ্রুপের সব সেটিংস, ফিল্টার, রুলস ফাইল হিসেবে ডাউনলোড করা বা নতুন গ্রুপে আপলোড করা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/export` - গ্রুপের সব ডেটা ডাউনলোড করে ফাইল নিন।\n"
        "• `/import` - সেভ করা ব্যাকআপ ফাইল আপলোড করে গ্রুপ রিস্টোর করুন।"
    ),
    "languages": (
        "🌍 **Languages (ভাষা নির্বাচন):**\n\n"
        "বটের ইন্টারফেস ও রিপ্লাই মেসেজের ভাষা পরিবর্তনের অপশন।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/setlang` - আপনার পছন্দের ভাষা (যেমন: বাংলা, ইংরেজি) বেছে নিন।"
    ),
    "locks": (
        "🔒 **Locks (নির্দিষ্ট কনটেন্ট লক):**\n\n"
        "গ্রুপে লিঙ্ক, ফটো, ভিডিও, ভয়েস, স্টিকার বা ফরওয়ার্ড মেসেজ পাঠানো বন্ধ রাখা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/lock links` - গ্রুপে সব ধরণের লিঙ্ক শেয়ার বন্ধ করুন।\n"
        "• `/lock photo` - ফটো পাঠানো বন্ধ করুন।\n"
        "• `/unlock <নাম>` - লক করা অপশন আবার চালু করুন।"
    ),
    "logchannels": (
        "📝 **Log Channels (লগ চ্যানেল মনিটরিং):**\n\n"
        "গ্রুপে কোন মেম্বার ব্যান হলো, কার মেসেজ ডিলিট হলো তা নজরদারির জন্য আলাদা প্রাইভেট চ্যানেলে সেভ রাখা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/logchannel` - বর্তমান লগ চ্যানেল চেক করুন।\n"
        "• `/setlog` - গ্রুপ অ্যাকশনের লগ পাঠানোর জন্য চ্যানেল সেট করুন।"
    ),
    "misc": (
        "⚙️ **Misc (বিবিধ দরকারি টুলস):**\n\n"
        "গ্রুপ ও মেম্বারদের সাধারণ প্রয়োজনীয় তথ্য জানার ফিচার।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/id` - আপনার নিজের এবং গ্রুপের টেলিগ্রাম ইউনিক আইডি জানুন।\n"
        "• `/info` - কোনো ইউজারের বিস্তারিত বায়ো ও প্রোফাইল ডাটা দেখুন।"
    ),
    "notes": (
        "📌 **Notes (প্রয়োজনীয় নোট সেভ):**\n\n"
        "গ্রুপের গুরুত্বপূর্ণ কোনো নোটিশ বা লিঙ্ক সেভ করে রাখা, যা `#নাম` লিখলেই সাথে সাথে পাওয়া যায়।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/save <নোটের_নাম> <মেসেজ>` - নতুন নোট সেভ করুন।\n"
        "• `/get <নোটের_নাম>` - সেভ করা নোট দেখুন।\n"
        "• `/notes` - সব সেভ করা নোটের লিস্ট।"
    ),
    "pin": (
        "📍 **Pin (মেসেজ পিন সিস্টেম):**\n\n"
        "গ্রুপের জরুরি কোনো নোটিশ বা পোস্ট সবার উপরে ঝুলিয়ে রাখার সুবিধা।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/pin` - যে মেসেজটি পিন করতে চান সেখানে রিপ্লাই দিয়ে এই কমান্ড দিন।\n"
        "• `/unpin` - বর্তমান পিন করা মেসেজ আনপিন করুন।\n"
        "• `/pinned` - বর্তমানে কোন মেসেজ পিন করা আছে তা সরাসরি দেখুন।"
    ),
    "privacy": (
        "🔐 **Privacy (ইউজার প্রাইভেসি ও নিরাপত্তা):**\n\n"
        "গ্রুপ মেম্বারদের ব্যক্তিগত গোপনীয়তা রক্ষা এবং টেলিগ্রাম সিকিউরিটি স্ট্যান্ডার্ড নিশ্চিত করার মডিউল।"
    ),
    "purges": (
        "🗑️ **Purges (ম্যাসিভ মেসেজ ডিলিট):**\n\n"
        "চ্যাট ক্লিয়ার করতে একসাথে শত শত অপ্রয়োজনীয় বা স্প্যাম মেসেজ চোখের পলকে মুছে ফেলার সিস্টেম।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/purge` - যে মেসেজ থেকে শুরু করে শেষ পর্যন্ত মুছতে চান, সেখানে রিপ্লাই করে কমান্ড দিন।"
    ),
    "reports": (
        "📢 **Reports (মেম্বার রিপোর্ট সিস্টেম):**\n\n"
        "গ্রুপে কোনো সমস্যা হলে সদস্যরা খুব সহজেই সব অ্যাডমিনদের ডেকে দৃষ্টি আকর্ষণ করতে পারে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• মেম্বাররা কোনো বাজে মেসেজে রিপ্লাই করে `@admin` অথবা `/report` লিখলেই গ্রুপের সকল অ্যাডমিনের কাছে নোটিফিকেশন পৌঁছে যাবে।"
    ),
    "rules": (
        "📜 **Rules (গ্রুপের কানুন ও নীতিমালা):**\n\n"
        "গ্রুপের নির্দিষ্ট নিয়মাবলী সেট করা, যাতে মেম্বাররা সহজেই এক ক্লিকে গ্রুপের নিয়ম দেখতে পারে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/rules` - গ্রুপের অফিসিয়াল নিয়মাবলী পড়ুন।\n"
        "• `/setrules <নিয়মগুলো>` - নতুন নিয়মাবলী সেট বা এডিট করুন।"
    ),
    "topics": (
        "💬 **Topics (টপিকস ও ফোরাম ম্যানেজমেন্ট):**\n\n"
        "টেলিগ্রামের ফোরাম বা সাব-টপিক গ্রুপগুলো সুশৃঙ্খলভাবে পরিচালনার মডিউল।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• নির্দিষ্ট সাব-টপিক বন্ধ, খোলা বা নির্দিষ্ট টপিকের ভেতরে মেসেজ ফিল্টারিং করা।"
    ),
    "warnings": (
        "⚠️ **Warnings (সতর্কবার্তা সিস্টেম):**\n\n"
        "নিয়ম না মানা সদস্যদের ওয়ার্নিং দেওয়া। ৩টি ওয়ার্ন পূর্ণ হলে মেম্বার অটো মিউট বা ব্যান হয়ে যাবে।\n\n"
        "**কমান্ডসমূহ:**\n"
        "• `/warn` - মেম্বারের মেসেজে রিপ্লাই করে সতর্কবার্তা দিন।\n"
        "• `/warns` - কোনো মেম্বার কয়টি ওয়ার্ন পেয়েছে তা দেখুন।\n"
        "• `/resetwarn` - ইউজারের সব ওয়ার্ন মাফ করে দিন।"
    ),
    "custominstances": (
        "⭐ **Custom Instances (পার্সোনাল ব্র্যান্ড বট):**\n\n"
        "নিজের গ্রুপ বা চ্যানেলের জন্য সম্পূর্ণ নিজস্ব নামে, প্রোফাইল ফটোতে ও লোগোতে একই সুবিধার পার্সোনাল বট তৈরি করা।\n\n"
        "• বিস্তারিত জানতে অ্যাডমিনের সাথে যোগাযোগ করুন: @rafimhossen"
    )
}

MODULE_LIST = [
    ("Admin", "admin"), ("Antiflood", "antiflood"), ("AntiRaid", "antiraid"),
    ("Approval", "approval"), ("Bans", "bans"), ("Blocklists", "blocklists"),
    ("CAPTCHA", "captcha"), ("Clean Comma", "cleancomma"), ("Clean Service", "cleanservice"),
    ("Connections", "connections"), ("Disabling", "disabling"), ("Federations", "federations"),
    ("Filters", "filters"), ("Formatting", "formatting"), ("Greetings", "greetings"),
    ("Import/Export", "importexport"), ("Languages", "languages"), ("Locks", "locks"),
    ("Log Channels", "logchannels"), ("Misc", "misc"), ("Notes", "notes"),
    ("Pin", "pin"), ("Privacy", "privacy"), ("Purges", "purges"),
    ("Reports", "reports"), ("Rules", "rules"), ("Topics", "topics")
]

def get_rose_help_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    btns = [types.InlineKeyboardButton(name, callback_data=f"info_{key}") for name, key in MODULE_LIST]
    markup.add(*btns)
    markup.row(
        types.InlineKeyboardButton("Warnings", callback_data="info_warnings"),
        types.InlineKeyboardButton("⭐ Custom Instances", callback_data="info_custominstances")
    )
    markup.row(types.InlineKeyboardButton("👨‍💻 Connect Admin (@rafimhossen)", url="https://t.me/rafimhossen"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def verify_subscription(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ ধন্যবাদ! আপনার ভেরিফিকেশন সফল হয়েছে।", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message, call.from_user)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো @rafimhossen3 চ্যানেলে জয়েন করেননি! দয়া করে আগে জয়েন করুন।", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("info_") or call.data == "back_to_menu")
def handle_module_details_callback(call):
    if not is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ আগে আমাদের চ্যানেলে জয়েন থাকতে হবে!", show_alert=True)
        bot.send_message(
            call.message.chat.id,
            "⚠️ **বট ব্যবহার করতে হলে অবশ্যই আমাদের অফিসিয়াল চ্যানেলে যুক্ত হতে হবে!**\n\nনিচের লিংকে জয়েন করে ভেরিফাই করুন:",
            reply_markup=get_join_markup(),
            parse_mode='Markdown'
        )
        return

    if call.data == "back_to_menu":
        bot.edit_message_text(
            "নিচের মডিউলগুলোতে চাপ দিয়ে বিস্তারিত জানুন:\n\nAll commands can be used with the following: `/` `!`",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_rose_help_menu()
        )
    else:
        key = call.data.replace("info_", "")
        detail_msg = MODULE_DETAILS.get(key, "📌 এই মডিউলটি সক্রিয় রয়েছে।")
        
        nav_markup = types.InlineKeyboardMarkup()
        nav_markup.row(
            types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu"),
            types.InlineKeyboardButton("👨‍💻 Support Admin", url="https://t.me/rafimhossen")
        )
        
        bot.edit_message_text(
            detail_msg,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=nav_markup,
            parse_mode='Markdown'
        )

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
        "নিচের মডিউলগুলোতে চাপ দিয়ে বিস্তারিত জানুন:\n\nAll commands can be used with the following: `/` `!`", 
        reply_markup=get_rose_help_menu()
    )

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    try:
        if message.chat.type == 'private':
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
                key = f"{chat_id}_{target.id}"
                USER_WARNS[key] = USER_WARNS.get(key, 0) + 1
                curr = USER_WARNS[key]
                if curr >= 3:
                    bot.restrict_chat_member(chat_id, target.id, permissions=types.ChatPermissions(can_send_messages=False))
                    bot.edit_message_text(f"🚫 [{target.first_name}](tg://user?id={target.id}) ৩ বার সতর্ক পেয়ে মিউট হয়েছেন!", chat_id, call.message.message_id, parse_mode='Markdown')
                    USER_WARNS[key] = 0
                else:
                    bot.edit_message_text(f"⚠️ [{target.first_name}](tg://user?id={target.id}) সতর্কবার্তা: **{curr}/3**", chat_id, call.message.message_id, parse_mode='Markdown')
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
def add_filter(message):
    if message.chat.type == 'private' or not is_group_admin(message.chat.id, message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ নিয়ম: `/addfilter শব্দ | উত্তর`", parse_mode='Markdown')
        return
    content = parts[1].split('|')
    if len(content) < 2:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাট: `/addfilter শব্দ | উত্তর`", parse_mode='Markdown')
        return
    kw = content[0].strip().lower()
    ans = content[1].strip()
    if message.chat.id not in GROUP_FILTERS:
        GROUP_FILTERS[message.chat.id] = {}
    GROUP_FILTERS[message.chat.id][kw] = ans
    bot.reply_to(message, f"🎯 ফিল্টার সেট হয়েছে: `{kw}`", parse_mode='Markdown')

@bot.message_handler(commands=['filters'])
def list_filters(message):
    if message.chat.type == 'private':
        return
    filters = GROUP_FILTERS.get(message.chat.id, {})
    if not filters:
        bot.reply_to(message, "📂 এই গ্রুপে কোনো কাস্টম ফিল্টার সেট নেই।")
        return
    txt = "📋 **গ্রুপের ফিল্টার তালিকা:**\n\n"
    for kw in filters.keys():
        txt += f"• `{kw}`\n"
    bot.reply_to(message, txt, parse_mode='Markdown')

@bot.message_handler(commands=['rules'])
def send_rules(message):
    bot.reply_to(message, "📜 **গ্রুপের নিয়মাবলী:**\n\n১. গ্রুপে লিঙ্ক শেয়ার বা স্প্যামিং করা নিষেধ।\n২. কাউকে অসম্মান করা যাবে না।")

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def group_filters_and_links(message):
    if not message.text:
        return
    is_admin = is_group_admin(message.chat.id, message.from_user.id) if message.from_user else False
    
    # অটো লিঙ্ক ব্লকার
    if re.search(r'(https?://[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+)', message.text):
        if not is_admin:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"⚠️ [{message.from_user.first_name}](tg://user?id={message.from_user.id}), গ্রুপে লিঙ্ক শেয়ার সম্পূর্ণ নিষিদ্ধ!", parse_mode='Markdown')
            except Exception:
                pass
            return

    # কাস্টম ফিল্টার চেক
    chat_filters = GROUP_FILTERS.get(message.chat.id, {})
    text_lower = message.text.lower()
    for kw, resp in chat_filters.items():
        if kw in text_lower:
            bot.reply_to(message, resp)
            break

if __name__ == '__main__':
    keep_alive()
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"Webhook clean error: {e}", flush=True)

    bot_user = bot.get_me()
    print(f"Logged in as @{bot_user.username}. Ready for actions!", flush=True)
    bot.infinity_polling(skip_pending=True)
