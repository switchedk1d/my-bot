import telebot
import requests
import re
import time
import json
import os
from datetime import datetime

# ================================================
# НАСТРОЙКИ (переменные окружения)
# ================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
PHONE_API_KEY = os.getenv('PHONE_API_KEY')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', 6482365079))  # Твой ID для логов
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)

# ================================================
# СТАТИСТИКА
# ================================================
total_checks = 0
api_working = {'numverify': False, 'omkar': False}

# ================================================
# ЛОГИРОВАНИЕ В TELEGRAM
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
# ЛОКАЛЬНАЯ БАЗА ОПЕРАТОРОВ РОССИИ
# ================================================
OPERATORS_RU = {
    '910': 'МТС', '911': 'МТС', '912': 'МТС', '913': 'МТС',
    '914': 'МТС', '915': 'МТС', '916': 'МТС', '917': 'МТС',
    '918': 'МТС', '919': 'МТС', '920': 'Мегафон', '921': 'Мегафон',
    '922': 'Мегафон', '923': 'Мегафон', '924': 'Мегафон',
    '925': 'Билайн', '926': 'Билайн', '927': 'Билайн',
    '928': 'Билайн', '929': 'Билайн', '930': 'Билайн',
    '931': 'Билайн', '932': 'Билайн', '933': 'Билайн',
    '934': 'Билайн', '935': 'Билайн', '936': 'Билайн',
    '937': 'Билайн', '938': 'Билайн', '939': 'Билайн',
    '950': 'Tele2', '951': 'Tele2', '952': 'Tele2',
    '953': 'Tele2', '954': 'Tele2', '955': 'Tele2',
    '956': 'Tele2', '957': 'Tele2', '958': 'Tele2',
    '959': 'Tele2', '960': 'МТС', '961': 'МТС',
    '962': 'МТС', '963': 'МТС', '964': 'МТС',
    '965': 'МТС', '966': 'МТС', '967': 'МТС',
    '968': 'МТС', '969': 'МТС', '980': 'МТС',
    '981': 'МТС', '982': 'МТС', '983': 'МТС',
    '984': 'МТС', '985': 'МТС', '986': 'МТС',
    '987': 'МТС', '988': 'МТС', '989': 'МТС',
    '990': 'Мегафон', '991': 'Мегафон', '992': 'Мегафон',
    '993': 'Мегафон', '994': 'Мегафон', '995': 'Мегафон',
    '996': 'Мегафон', '997': 'Мегафон', '998': 'Мегафон',
    '999': 'Мегафон'
}

def get_operator_ru(phone):
    clean = re.sub(r'[^0-9]', '', phone)
    if clean.startswith('7') or clean.startswith('8') or clean.startswith('9'):
        if len(clean) >= 10:
            code = clean[1:4] if clean.startswith('7') or clean.startswith('8') else clean[:3]
            return OPERATORS_RU.get(code, None)
    return None

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
    '90': 'Турция', '380': 'Украина', '375': 'Беларусь',
    '995': 'Грузия', '994': 'Азербайджан', '374': 'Армения',
    '998': 'Узбекистан', '992': 'Таджикистан', '996': 'Кыргызстан',
    '993': 'Туркменистан', '371': 'Латвия', '372': 'Эстония',
    '370': 'Литва', '373': 'Молдова', '40': 'Румыния',
    '36': 'Венгрия', '420': 'Чехия', '421': 'Словакия',
    '48': 'Польша', '30': 'Греция', '45': 'Дания',
    '47': 'Норвегия', '358': 'Финляндия', '353': 'Ирландия',
    '351': 'Португалия', '54': 'Аргентина', '56': 'Чили',
    '57': 'Колумбия', '52': 'Мексика', '51': 'Перу',
    '27': 'ЮАР', '234': 'Нигерия', '20': 'Египет',
    '212': 'Марокко', '216': 'Тунис', '92': 'Пакистан',
    '94': 'Шри-Ланка', '60': 'Малайзия', '62': 'Индонезия',
    '63': 'Филиппины', '64': 'Новая Зеландия', '65': 'Сингапур',
    '971': 'ОАЭ', '966': 'Саудовская Аравия', '972': 'Израиль',
    '976': 'Монголия', '977': 'Непал'
}

def get_country_by_code(phone):
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if phone.startswith(code):
            return COUNTRY_CODES[code], code
    return 'Неизвестно', ''

# ================================================
# ПРОВЕРКА ТЕЛЕФОНА
# ================================================

def is_obviously_fake(phone):
    clean = re.sub(r'[^0-9]', '', phone)
    if len(set(clean)) == 1:
        return True
    fake_patterns = ['123456789', '1234567890', '0987654321', '9876543210',
                     '1111111111', '2222222222', '3333333333', '4444444444',
                     '5555555555', '6666666666', '7777777777', '8888888888',
                     '9999999999', '0000000000']
    for pattern in fake_patterns:
        if pattern in clean:
            return True
    for i in range(0, len(clean) - 5):
        if len(set(clean[i:i+6])) == 1:
            return True
    if len(clean) < 10 or len(clean) > 15:
        return True
    return False

def check_phone(phone):
    global total_checks
    total_checks += 1
    
    log_action('PHONE_CHECK', phone)
    
    clean = re.sub(r'[^0-9]', '', phone.strip())
    
    if is_obviously_fake(phone):
        return (f"📱 *ПРОВЕРКА ТЕЛЕФОНА*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕ ВАЛИДНЫЙ\n"
                f"📞 *Номер:* {phone}\n"
                f"💡 *Причина:* Повторяющиеся цифры или тестовый номер\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    if len(clean) < 10 or len(clean) > 15:
        return (f"📱 *ПРОВЕРКА ТЕЛЕФОНА*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕ ВАЛИДНЫЙ\n"
                f"📞 *Номер:* {phone}\n"
                f"💡 *Причина:* Длина {len(clean)} (нужно 10-15)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")

    country, code = get_country_by_code(clean)
    formatted = '+' + clean
    
    # Пробуем omkar.cloud
    try:
        url = f"https://carrier-lookup-api.omkar.cloud/lookup?phone={formatted}"
        headers = {'API-Key': PHONE_API_KEY}
        response = requests.get(url, headers=headers, timeout=8)
        data = response.json()
        
        if data.get('is_valid_number', False):
            api_working['omkar'] = True
            line_type = data.get('line_type', 'Неизвестно')
            carrier = data.get('carrier', 'Неизвестно')
            
            if line_type.lower() == 'mobile':
                status_text = "✅ НАСТОЯЩИЙ (реальный номер)"
            elif line_type.lower() == 'voip':
                status_text = "⚠️ ВИРТУАЛЬНЫЙ (VOIP номер)"
            elif line_type.lower() == 'landline':
                status_text = "✅ СТАЦИОНАРНЫЙ"
            else:
                status_text = "✅ ВАЛИДНЫЙ"
            
            return (f"📱 *ПРОВЕРКА ТЕЛЕФОНА*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{status_text}\n"
                    f"📞 *Номер:* {data.get('phone_number', formatted)}\n"
                    f"🌍 *Страна:* {data.get('country_code', country)}\n"
                    f"📡 *Оператор:* {carrier}\n"
                    f"🔢 *Тип:* {line_type}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔄 *Источник:* omkar.cloud\n"
                    f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    except Exception as e:
        log_action('OMKAR_ERROR', str(e))
        send_log(f"⚠️ omkar.cloud не ответил: {e}")
    
    # FALLBACK — локальная проверка с базой операторов
    operator = get_operator_ru(clean)
    if operator:
        return (f"📱 *ПРОВЕРКА ТЕЛЕФОНА*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *Статус:* ВАЛИДНЫЙ (локально)\n"
                f"📞 *Номер:* {formatted}\n"
                f"🌍 *Страна:* {country}\n"
                f"📡 *Оператор:* {operator} (локальная база)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 *Источник:* Локальная проверка\n"
                f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    else:
        return (f"📱 *ПРОВЕРКА ТЕЛЕФОНА*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Статус:* НЕ ОПРЕДЕЛЁН\n"
                f"📞 *Номер:* {formatted}\n"
                f"🌍 *Страна:* {country}\n"
                f"💡 *Оператор не найден в локальной базе*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🔄 *Источник:* Локальная проверка\n"
                f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# ================================================
# КОМАНДА /stats
# ================================================

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    stats_text = (
        f"📊 *СТАТИСТИКА БОТА*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Всего проверок: {total_checks}\n"
        f"🌐 Numverify: {'✅' if api_working['numverify'] else '❌'}\n"
        f"☁️ Omkar.cloud: {'✅' if api_working['omkar'] else '❌'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )
    bot.reply_to(message, stats_text, parse_mode='Markdown')

# ================================================
# ОСТАЛЬНЫЕ ПРОВЕРКИ (EMAIL, CARD, IP, SITE)
# ================================================

def check_email(email):
    # ... (оставляем как есть)
    pass

def check_card(card):
    # ... (оставляем как есть)
    pass

def check_ip(ip):
    # ... (оставляем как есть)
    pass

def check_site(url):
    # ... (оставляем как есть)
    pass

# ================================================
# КОМАНДЫ
# ================================================

@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):
    bot.reply_to(message, 
        "🔍 *БОТ-ПРОВЕРЩИК v5.0*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *КОМАНДЫ:*\n"
        "📱 `/phone +79229244035` — проверка телефона\n"
        "📧 `/email test@mail.com` — проверка email\n"
        "🌐 `/ip 8.8.8.8` — информация по IP\n"
        "💳 `/card 4111111111111111` — проверка карты\n"
        "🌍 `/site google.com` — проверка сайта\n"
        "📊 `/stats` — статистика бота\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Новая локальная база операторов!\n"
        "✅ Логирование ошибок в Telegram!",
        parse_mode='Markdown')

@bot.message_handler(commands=['phone'])
def phone_cmd(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ /phone +79229244035")
            return
        bot.reply_to(message, check_phone(' '.join(args[1:])), parse_mode='Markdown')
    except Exception as e:
        send_log(f"Ошибка в phone_cmd: {e}")
        bot.reply_to(message, "⚠️ Ошибка, попробуй ещё раз")

@bot.message_handler(commands=['email'])
def email_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /email test@mail.com")
        return
    bot.reply_to(message, check_email(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['ip'])
def ip_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /ip 8.8.8.8")
        return
    bot.reply_to(message, check_ip(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['card'])
def card_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /card 4111111111111111")
        return
    bot.reply_to(message, check_card(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['site'])
def site_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ /site google.com")
        return
    bot.reply_to(message, check_site(args[1]), parse_mode='Markdown')

# ================================================
# ЗАПУСК
# ================================================

print("=" * 60)
print("  🤖 БОТ-ПРОВЕРЩИК v5.0 (GitHub)")
print("=" * 60)
print("✅ Бот запущен!")
print("📌 Добавлено:")
print("  ✅ /stats — статистика")
print("  ✅ Локальная база операторов")
print("  ✅ Логирование в Telegram")
print("=" * 60)

send_log("🚀 Бот успешно запущен на GitHub!")

if __name__ == "__main__":
    bot.infinity_polling()
