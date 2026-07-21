import telebot
import requests
import re
import time
import json
import os
from datetime import datetime

# ================================================
# НАСТРОЙКИ
# ================================================
BOT_TOKEN = os.getenv('BOT_TOKEN')
PHONE_API_KEY = os.getenv('PHONE_API_KEY')

# Коды стран для локальной проверки
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
    '212': 'Марокко', '216': 'Тунис', '90': 'Турция',
    '92': 'Пакистан', '94': 'Шри-Ланка', '60': 'Малайзия',
    '62': 'Индонезия', '63': 'Филиппины', '64': 'Новая Зеландия',
    '65': 'Сингапур', '971': 'ОАЭ', '966': 'Саудовская Аравия',
    '972': 'Израиль', '976': 'Монголия', '977': 'Непал'
}
# ================================================

bot = telebot.TeleBot(BOT_TOKEN)

LOG_FILE = 'bot_log.txt'

def log_action(action, data):
    """Запись в лог"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {action}: {data}\n")
    except:
        pass

def get_country_by_code(phone):
    """Определяет страну по коду"""
    for code in sorted(COUNTRY_CODES.keys(), key=len, reverse=True):
        if phone.startswith(code):
            return COUNTRY_CODES[code], code
    return 'Неизвестно', ''

# ================================================
# ПРОВЕРКА ТЕЛЕФОНА (omkar + FALLBACK)
# ================================================

def is_obviously_fake(phone):
    """Проверяет, не является ли номер заведомо фейковым"""
    clean = re.sub(r'[^0-9]', '', phone)
    
    # 1. Все цифры одинаковые
    if len(set(clean)) == 1:
        return True
    
    # 2. Типичные фейковые паттерны
    fake_patterns = [
        '123456789', '1234567890', '0987654321', '9876543210',
        '1111111111', '2222222222', '3333333333', '4444444444',
        '5555555555', '6666666666', '7777777777', '8888888888',
        '9999999999', '0000000000'
    ]
    for pattern in fake_patterns:
        if pattern in clean:
            return True
    
    # 3. Проверка на повторяющиеся блоки (например, 123123123)
    for i in range(0, len(clean) - 5):
        if len(set(clean[i:i+6])) == 1:
            return True
    
    # 4. Слишком короткий (меньше 10 цифр)
    if len(clean) < 10:
        return True
    
    # 5. Слишком длинный (больше 15 цифр)
    if len(clean) > 15:
        return True
    
    return False
    
def check_phone(phone):
    """Проверка телефона: omkar.cloud API + локальный fallback"""
    log_action('PHONE_CHECK', phone)
    
    # Очищаем номер
    clean = re.sub(r'[^0-9]', '', phone.strip())
    
    # Проверка на фейк (паттерны)
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
    
    # ================================================
    # ПРОБУЕМ OMKAR.CLOUD API
    # ================================================
    try:
        url = f"https://carrier-lookup-api.omkar.cloud/lookup?phone={formatted}"
        headers = {'API-Key': PHONE_API_KEY}
        response = requests.get(url, headers=headers, timeout=8)
        data = response.json()
        
        if data.get('is_valid_number', False):
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
        else:
            log_action('OMKAR', f'API вернул invalid для {formatted}')
    except Exception as e:
        log_action('OMKAR_ERROR', str(e))
    
    # ================================================
    # FALLBACK — локальная проверка
    # ================================================
    if clean.startswith('668'):
        type_hint = "⚠️ ВИРТУАЛЬНЫЙ (локальная проверка)"
    elif clean.startswith('7') and len(clean) == 11:
        type_hint = "❓ Российский номер (проверьте вручную)"
    else:
        type_hint = "❓ Не определён (API недоступны)"
    
    return (f"📱 *ПРОВЕРКА ТЕЛЕФОНА*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Статус:* НЕ ОПРЕДЕЛЁН (API недоступен)\n"
            f"📞 *Номер:* {formatted}\n"
            f"🌍 *Страна:* {country}\n"
            f"🔢 *Тип:* {type_hint}\n"
            f"💡 *Проверьте номер вручную*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 *Источник:* Локальная проверка\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# ================================================
# ПРОВЕРКА EMAIL
# ================================================

def check_email(email):
    """Проверка email: формат + фейковые домены"""
    log_action('EMAIL_CHECK', email)
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return (f"📧 *ПРОВЕРКА EMAIL*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕВАЛИДНЫЙ\n"
                f"📧 *Email:* {email}\n"
                f"💡 *Причина:* Неправильный формат\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    domain = email.split('@')[1].lower()
    fake_domains = ['tempmail.com', '10minutemail.com', 'mailinator.com',
                    'yopmail.com', 'guerrillamail.com', 'throwawaymail.com',
                    'temp-mail.org', 'dispostable.com', 'sharklasers.com']
    
    if domain in fake_domains:
        return (f"📧 *ПРОВЕРКА EMAIL*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⚠️ *Статус:* ФЕЙКОВЫЙ\n"
                f"📧 *Email:* {email}\n"
                f"📮 *Домен:* {domain}\n"
                f"💡 *Причина:* Домен для временной почты\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    # Проверка существования домена
    try:
        import socket
        socket.gethostbyname(domain)
        domain_exists = True
    except:
        domain_exists = False
    
    if not domain_exists:
        return (f"📧 *ПРОВЕРКА EMAIL*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕВАЛИДНЫЙ\n"
                f"📧 *Email:* {email}\n"
                f"📮 *Домен:* {domain}\n"
                f"💡 *Причина:* Домен не существует\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    return (f"📧 *ПРОВЕРКА EMAIL*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Статус:* ВАЛИДНЫЙ\n"
            f"📧 *Email:* {email}\n"
            f"📮 *Домен:* {domain}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# ================================================
# ПРОВЕРКА КАРТЫ (алгоритм Луна + BIN)
# ================================================

def check_card(card):
    """Проверка банковской карты"""
    log_action('CARD_CHECK', card)
    
    clean = re.sub(r'[\s\-]', '', card.strip())
    
    if not clean.isdigit():
        return (f"💳 *ПРОВЕРКА КАРТЫ*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕВАЛИДНАЯ\n"
                f"💡 *Причина:* Только цифры\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    if len(clean) not in [15, 16]:
        return (f"💳 *ПРОВЕРКА КАРТЫ*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕВАЛИДНАЯ\n"
                f"💡 *Причина:* Длина {len(clean)} (нужно 15 или 16)\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    # Алгоритм Луна
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
        return (f"💳 *ПРОВЕРКА КАРТЫ*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ *Статус:* НЕВАЛИДНАЯ\n"
                f"💡 *Причина:* Ошибка алгоритма Луна\n"
                f"━━━━━━━━━━━━━━━━━━━━━━")
    
    # Определяем систему
    first = clean[0]
    if first == '4':
        system = 'VISA'
    elif first == '5':
        system = 'MasterCard'
    elif first == '3' and clean[1] in '47':
        system = 'American Express'
    elif first == '3':
        system = 'JCB'
    elif first == '6':
        system = 'Discover'
    else:
        system = 'Неизвестно'
    
    # Определяем банк через BIN API
    bank_info = ''
    try:
        bin_number = clean[:6]
        response = requests.get(f"https://binlist.net/json/{bin_number}", timeout=5)
        data = response.json()
        if data.get('bank'):
            bank_info = (f"\n🏦 *Банк:* {data['bank'].get('name', 'Неизвестно')}\n"
                         f"🌍 *Страна:* {data.get('country', {}).get('name', 'Неизвестно')}")
    except:
        pass
    
    return (f"💳 *ПРОВЕРКА КАРТЫ*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *Статус:* ВАЛИДНАЯ\n"
            f"💳 *Система:* {system}\n"
            f"🔢 *Номер:* {clean[:4]}****{clean[-4:]}{bank_info}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

# ================================================
# ПРОВЕРКА IP
# ================================================

def check_ip(ip):
    """Проверка IP через ip-api.com"""
    log_action('IP_CHECK', ip)
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
        data = response.json()
        
        if data.get('status') == 'success':
            return (f"🌐 *ИНФОРМАЦИЯ ПО IP*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📡 *IP:* {ip}\n"
                    f"📍 *Страна:* {data.get('country', 'Неизвестно')}\n"
                    f"🏙️ *Город:* {data.get('city', 'Неизвестно')}\n"
                    f"📡 *Провайдер:* {data.get('isp', 'Неизвестно')}\n"
                    f"🌐 *Регион:* {data.get('regionName', 'Неизвестно')}\n"
                    f"🧭 *Координаты:* {data.get('lat', '')}, {data.get('lon', '')}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        else:
            return f"❌ IP не найден или приватный: {ip}"
    except Exception as e:
        return f"❌ Ошибка проверки IP: {e}"

# ================================================
# ПРОВЕРКА САЙТА
# ================================================

def check_site(url):
    """Проверка сайта"""
    log_action('SITE_CHECK', url)
    
    if not url.startswith('http'):
        url = 'http://' + url
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10, allow_redirects=True)
        response_time = round((time.time() - start_time) * 1000, 2)
        
        status = response.status_code
        if 200 <= status < 300:
            status_text = "✅ РАБОТАЕТ"
        elif 300 <= status < 400:
            status_text = "🔄 ПЕРЕНАПРАВЛЕНИЕ"
        elif 400 <= status < 500:
            status_text = "⚠️ ОШИБКА КЛИЕНТА"
        elif 500 <= status < 600:
            status_text = "❌ ОШИБКА СЕРВЕРА"
        else:
            status_text = "❓ НЕИЗВЕСТНО"
        
        return (f"🌍 *ПРОВЕРКА САЙТА*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 *URL:* {url}\n"
                f"📊 *Статус:* {status} {status_text}\n"
                f"⏱️ *Время ответа:* {response_time} мс\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    except requests.exceptions.Timeout:
        return f"❌ Сайт не отвечает (таймаут)\n🌐 {url}"
    except requests.exceptions.ConnectionError:
        return f"❌ Сайт не найден\n🌐 {url}"
    except Exception as e:
        return f"❌ Ошибка проверки: {e}"

# ================================================
# КОМАНДЫ
# ================================================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message, 
        "👋 *Привет! Я БОТ-ПРОВЕРЩИК v4.2*\n\n"
        "📌 *Я умею проверять:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📱 Телефоны — `/phone`\n"
        "📧 Email — `/email`\n"
        "🌐 IP-адреса — `/ip`\n"
        "💳 Банковские карты — `/card`\n"
        "🌍 Сайты — `/site`\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📖 Напиши `/help` для подробной инструкции",
        parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, 
        "🔍 *ПОДРОБНАЯ ИНСТРУКЦИЯ*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📱 `/phone +79229244035` — проверка телефона\n"
        "   → оператор, тип, страна\n\n"
        "📧 `/email test@mail.com` — проверка email\n"
        "   → формат, домен, фейк\n\n"
        "🌐 `/ip 8.8.8.8` — информация по IP\n"
        "   → страна, город, провайдер\n\n"
        "💳 `/card 4111111111111111` — проверка карты\n"
        "   → система, банк, валидность\n\n"
        "🌍 `/site google.com` — проверка сайта\n"
        "   → статус, время\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔄 Если API не отвечает — бот проверяет локально!",
        parse_mode='Markdown')

@bot.message_handler(commands=['phone'])
def phone_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши: `/phone +79229244035`", parse_mode='Markdown')
        return
    bot.reply_to(message, check_phone(' '.join(args[1:])), parse_mode='Markdown')

@bot.message_handler(commands=['email'])
def email_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши: `/email test@mail.com`", parse_mode='Markdown')
        return
    bot.reply_to(message, check_email(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['ip'])
def ip_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши: `/ip 8.8.8.8`", parse_mode='Markdown')
        return
    bot.reply_to(message, check_ip(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['card'])
def card_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши: `/card 4111111111111111`", parse_mode='Markdown')
        return
    bot.reply_to(message, check_card(args[1]), parse_mode='Markdown')

@bot.message_handler(commands=['site'])
def site_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "❌ Напиши: `/site google.com`", parse_mode='Markdown')
        return
    bot.reply_to(message, check_site(args[1]), parse_mode='Markdown')

# ================================================
# ЗАПУСК
# ================================================

print("=" * 60)
print("  🤖 БОТ-ПРОВЕРЩИК v4.2")
print("=" * 60)
print("✅ Бот запущен!")
print(f"📌 Токен: {BOT_TOKEN[:10]}...")
print(f"📌 API-ключ omkar: {PHONE_API_KEY[:10]}...")
print("=" * 60)
print("📌 ДОСТУПНЫЕ КОМАНДЫ:")
print("  /phone +79229244035  — проверка телефона (API + FALLBACK)")
print("  /email test@mail.com — проверка email")
print("  /ip 8.8.8.8          — информация по IP")
print("  /card 4111111111111111 — проверка карты")
print("  /site google.com     — проверка сайта")
print("=" * 60)
print("🔄 Если API не отвечает — бот проверяет локально!")
print("=" * 60)

# ================================================
# ЗАПУСК
# ================================================

print("=" * 60)
print("  🤖 БОТ-ПРОВЕРЩИК v4.2")
print("=" * 60)
print("✅ Бот запущен!")
print(f"📌 Токен: {BOT_TOKEN[:10]}...")
print("=" * 60)

if __name__ == "__main__":
    bot.infinity_polling()
