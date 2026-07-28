import telebot
import requests
import re
import time
import json
import os
import ssl
import urllib3
import socket
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ОТКЛЮЧАЕМ SSL-ПРОВЕРКУ
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================
# НАСТРОЙКИ (ЗАМЕНИ НА СВОИ!)
# ================================================
BOT_TOKEN = '8731103715:AAENjKYBq8rN7dwVU8gLKBz-X_ixIAmazdY'
PHONE_API_KEY = 'ok_7f681d2b7d574e4e5d8185bf5df6ba57'
ADMIN_CHAT_ID = 6482365079
# ================================================

session = requests.Session()
session.verify = False
bot = telebot.TeleBot(BOT_TOKEN)
bot.session = session

# ================================================
# СТАТИСТИКА
# ================================================
STATS_FILE = 'stats.json'

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_user_stats(user_id):
    stats = load_stats()
    user_id_str = str(user_id)
    if user_id_str not in stats:
        stats[user_id_str] = {
            'total_checks': 0,
            'phone_checks': 0,
            'email_checks': 0,
            'card_checks': 0,
            'ip_checks': 0,
            'site_checks': 0
        }
    return stats, stats[user_id_str]

def update_user_stats(user_id, check_type):
    stats = load_stats()
    user_id_str = str(user_id)
    if user_id_str not in stats:
        stats[user_id_str] = {
            'total_checks': 0,
            'phone_checks': 0,
            'email_checks': 0,
            'card_checks': 0,
            'ip_checks': 0,
            'site_checks': 0
        }
    stats[user_id_str]['total_checks'] += 1
    if check_type == 'phone':
        stats[user_id_str]['phone_checks'] += 1
    elif check_type == 'email':
        stats[user_id_str]['email_checks'] += 1
    elif check_type == 'card':
        stats[user_id_str]['card_checks'] += 1
    elif check_type == 'ip':
        stats[user_id_str]['ip_checks'] += 1
    elif check_type == 'site':
        stats[user_id_str]['site_checks'] += 1
    save_stats(stats)

# ================================================
# ЛОГИ
# ================================================
def send_log(text):
    try:
        bot.send_message(ADMIN_CHAT_ID, f"📋 *ЛОГ:*\n{text}", parse_mode='Markdown')
    except:
        pass

def log_action(action, data):
    try:
        with open('bot_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action}: {data}\n")
    except:
        pass

# ================================================
# КОДЫ СТРАН
# ================================================
COUNTRY_CODES = {
    '7': 'Россия', '1': 'США/Канада', '44': 'Великобритания',
    '49': 'Германия', '33': 'Франция', '86': 'Китай',
    '91': 'Индия', '81': 'Япония', '55': 'Бразилия',
    '66': 'Таиланд', '34': 'Испания', '39': 'Италия',
    '61': 'Австралия', '82': 'Южная Корея', '31': 'Нидерланды',
    '46': 'Швеция', '41': 'Швейцария', '48': 'Польша',
    '90': 'Турция', '380': 'Украина', '375': 'Беларусь'
}

def get_country(phone):
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if phone.startswith(code):
            return COUNTRY_CODES[code]
    return 'Неизвестно'

# ================================================
# ПРОВЕРКА ТЕЛЕФОНА
# ================================================

def check_phone(phone):
    log_action('PHONE_CHECK', phone)
    clean = re.sub(r'[^0-9]', '', phone.strip())
    if len(clean) < 10 or len(clean) > 15:
        return f"❌ Невалидный номер (длина {len(clean)})"
    country = get_country(clean)
    formatted = '+' + clean
    return f"✅ Номер валидный!\n📞 {formatted}\n🌍 Страна: {country}"

# ================================================
# ПРОВЕРКА EMAIL
# ================================================

def check_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return "❌ Невалидный email"
    domain = email.split('@')[1].lower()
    fake = ['tempmail.com', '10minutemail.com', 'mailinator.com', 'yopmail.com']
    if domain in fake:
        return f"⚠️ Фейковый email! Домен: {domain}"
    return f"✅ Email валидный!\n📧 {email}\n📮 {domain}"

# ================================================
# ПРОВЕРКА КАРТЫ
# ================================================

def check_card(card):
    clean = re.sub(r'[\s\-]', '', card)
    if not clean.isdigit() or len(clean) not in [15, 16]:
        return "❌ Невалидная карта"
    
    def luhn(n):
        s = 0
        for i, d in enumerate(n[::-1]):
            x = int(d)
            if i % 2:
                x *= 2
                if x > 9:
                    x -= 9
            s += x
        return s % 10 == 0
    
    if not luhn(clean):
        return "❌ Невалидная карта (ошибка алгоритма)"
    
    system = {'4': 'VISA', '5': 'MasterCard', '3': 'AmEx', '6': 'Discover'}.get(clean[0], 'Неизвестно')
    return f"✅ Карта валидна!\n💳 {system}\n🔢 {clean[:4]}****{clean[-4:]}"

# ================================================
# ПРОВЕРКА IP
# ================================================

def check_ip(ip):
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        data = r.json()
        if data.get('status') == 'success':
            return f"🌍 IP: {ip}\n📍 {data.get('country')}\n🏙️ {data.get('city')}\n📡 {data.get('isp')}"
        return "❌ IP не найден"
    except:
        return "❌ Ошибка проверки IP"

# ================================================
# ПРОВЕРКА САЙТА
# ================================================

def check_site(url):
    if not url.startswith('http'):
        url = 'http://' + url
    try:
        r = requests.get(url, timeout=5)
        return f"✅ Сайт работает!\n🌐 {url}\n📊 Статус: {r.status_code}"
    except:
        return f"❌ Сайт не отвечает\n🌐 {url}"

# ================================================
# WHOIS
# ================================================

def check_whois(domain):
    try:
        import whois
        w = whois.whois(domain)
        return (f"🌐 WHOIS: {domain}\n"
                f"📅 Создан: {w.creation_date}\n"
                f"📅 Истекает: {w.expiration_date}\n"
                f"👤 Регистратор: {w.registrar}")
    except:
        return f"❌ Не удалось получить WHOIS для {domain}"

# ================================================
# SSL
# ================================================

def check_ssl(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return f"🔒 SSL-сертификат {domain}\n📅 Истекает: {cert['notAfter']}"
    except:
        return f"❌ Не удалось проверить SSL для {domain}"

# ================================================
# МАССОВАЯ ПРОВЕРКА
# ================================================

def mass_check(numbers):
    results = []
    for num in numbers[:20]:
        result = check_phone(num)
        results.append(f"{num}: {result[:50]}...")
        time.sleep(0.3)
    return "\n".join(results)

# ================================================
# ИНЛАЙН-КНОПКИ
# ================================================

def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📱 Проверить номер", callback_data="phone"),
        InlineKeyboardButton("📧 Проверить email", callback_data="email"),
        InlineKeyboardButton("💳 Проверить карту", callback_data="card"),
        InlineKeyboardButton("🌐 Проверить IP", callback_data="ip"),
        InlineKeyboardButton("🌍 Проверить сайт", callback_data="site"),
        InlineKeyboardButton("🌐 WHOIS", callback_data="whois"),
        InlineKeyboardButton("🔒 SSL", callback_data="ssl"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        InlineKeyboardButton("📂 Массовая проверка", callback_data="mass")
    )
    return keyboard

# ================================================
# КОМАНДЫ
# ================================================

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.send_message(message.chat.id,
        "🔍 *БОТ-ПРОВЕРЩИК @hinewrock*\nВыбери действие:",
        parse_mode='Markdown',
        reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "phone":
        bot.send_message(chat_id, "📱 Отправь номер:\n`/phone +79229244035`", parse_mode='Markdown')
    elif call.data == "email":
        bot.send_message(chat_id, "📧 Отправь email:\n`/email test@mail.com`", parse_mode='Markdown')
    elif call.data == "card":
        bot.send_message(chat_id, "💳 Отправь карту:\n`/card 4111111111111111`", parse_mode='Markdown')
    elif call.data == "ip":
        bot.send_message(chat_id, "🌐 Отправь IP:\n`/ip 8.8.8.8`", parse_mode='Markdown')
    elif call.data == "site":
        bot.send_message(chat_id, "🌍 Отправь сайт:\n`/site google.com`", parse_mode='Markdown')
    elif call.data == "whois":
        bot.send_message(chat_id, "🌐 Отправь домен:\n`/whois google.com`", parse_mode='Markdown')
    elif call.data == "ssl":
        bot.send_message(chat_id, "🔒 Отправь домен:\n`/ssl google.com`", parse_mode='Markdown')
    elif call.data == "stats":
        bot.send_message(chat_id, "📊 Напиши:\n`/stats`", parse_mode='Markdown')
    elif call.data == "mass":
        bot.send_message(chat_id, "📂 Отправь номера через запятую:")
        bot.register_next_step_handler(call.message, mass_check_handler)
    
    bot.answer_callback_query(call.id)

def mass_check_handler(message):
    try:
        raw = message.text.replace('\n', ',').replace(' ', ',')
        numbers = [n.strip() for n in raw.split(',') if n.strip()]
        result = mass_check(numbers)
        bot.reply_to(message, f"📊 *МАССОВАЯ ПРОВЕРКА*\n━━━━━━━━━━━━━━━━━━━━━━\n{result}", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# ================================================
# ОСНОВНЫЕ КОМАНДЫ
# ================================================

@bot.message_handler(commands=['phone'])
def phone_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /phone +79229244035")
        return
    user_id = message.from_user.id
    update_user_stats(user_id, 'phone')
    bot.reply_to(message, check_phone(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['email'])
def email_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /email test@mail.com")
        return
    user_id = message.from_user.id
    update_user_stats(user_id, 'email')
    bot.reply_to(message, check_email(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['card'])
def card_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /card 4111111111111111")
        return
    user_id = message.from_user.id
    update_user_stats(user_id, 'card')
    bot.reply_to(message, check_card(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['ip'])
def ip_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /ip 8.8.8.8")
        return
    user_id = message.from_user.id
    update_user_stats(user_id, 'ip')
    bot.reply_to(message, check_ip(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['site'])
def site_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /site google.com")
        return
    user_id = message.from_user.id
    update_user_stats(user_id, 'site')
    bot.reply_to(message, check_site(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['whois'])
def whois_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /whois google.com")
        return
    bot.reply_to(message, check_whois(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['ssl'])
def ssl_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /ssl google.com")
        return
    bot.reply_to(message, check_ssl(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    stats, user_stats = get_user_stats(user_id)
    bot.reply_to(message,
        f"📊 *ТВОЯ СТАТИСТИКА*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Всего: {user_stats['total_checks']}\n"
        f"📱 Телефонов: {user_stats['phone_checks']}\n"
        f"📧 Email: {user_stats['email_checks']}\n"
        f"💳 Карт: {user_stats['card_checks']}\n"
        f"🌐 IP: {user_stats['ip_checks']}\n"
        f"🌍 Сайтов: {user_stats['site_checks']}",
        parse_mode='Markdown')

# ================================================
# ЗАПУСК
# ================================================

print("=" * 50)
print("  🤖 БОТ-ПРОВЕРЩИК v6.0")
print("=" * 50)
print("✅ Бот запущен!")
print("📌 Инлайн-кнопки, WHOIS, SSL, массовая проверка — активны!")
print("=" * 50)

bot.infinity_polling()
