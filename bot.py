import telebot
import requests
import re
import time
import json
import os
import ssl
import urllib3
from datetime import datetime

# ОТКЛЮЧАЕМ SSL-ПРОВЕРКУ ДЛЯ ПЛОХОГО ИНТЕРНЕТА
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================================================
# НАСТРОЙКИ
# ================================================
BOT_TOKEN = '8731103715:AAENjKYBq8rN7dwVU8gLKBz-X_ixIAmazdY'
PHONE_API_KEY = 'ok_7f681d2b7d574e4e5d8185bf5df6ba57'
ADMIN_CHAT_ID = 6482365079  # ТВОЙ ID (для логов)

# ПРОКСИ (ЕСЛИ НУЖЕН — РАСКОММЕНТИРУЙ И ВСТАВЬ СВОЙ)
# PROXY = {
#     'http': 'https://77.110.102.252',
#     'https': 'https://47.243.92.199'
# }
# ================================================

# СОЗДАЁМ СЕССИЮ (С ПРОКСИ ИЛИ БЕЗ)
session = requests.Session()
# if PROXY:
#     session.proxies.update(PROXY)
session.verify = False
bot = telebot.TeleBot(BOT_TOKEN)
bot.session = session

# ================================================
# ФАЙЛ ДЛЯ СТАТИСТИКИ
# ================================================
STATS_FILE = 'stats.json'

def load_stats():
    """Загружает статистику из файла"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_stats(stats):
    """Сохраняет статистику в файл"""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_user_stats(user_id):
    """Получает статистику конкретного пользователя"""
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
    """Обновляет статистику пользователя"""
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
    """Определяет оператора по коду DEF (первые 3 цифры после 7/8/9)"""
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
    '30': 'Греция', '45': 'Дания', '47': 'Норвегия',
    '358': 'Финляндия', '353': 'Ирландия', '351': 'Португалия',
    '54': 'Аргентина', '56': 'Чили', '57': 'Колумбия',
    '52': 'Мексика', '51': 'Перу', '27': 'ЮАР',
    '234': 'Нигерия', '20': 'Египет', '212': 'Марокко',
    '216': 'Тунис', '92': 'Пакистан', '94': 'Шри-Ланка',
    '60': 'Малайзия', '62': 'Индонезия', '63': 'Филиппины',
    '64': 'Новая Зеландия', '65': 'Сингапур', '971': 'ОАЭ',
    '966': 'Саудовская Аравия', '972': 'Израиль', '976': 'Монголия',
    '977': 'Непал'
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
        response = requests.get(url, headers=headers, timeout=8, verify=False)
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
# ПРОВЕРКА EMAIL
# ================================================

def check_email(email):
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
# ПРОВЕРКА КАРТЫ
# ================================================

def check_card(card):
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
    
    bank_info = ''
    try:
        bin_number = clean[:6]
        response = requests.get(f"https://binlist.net/json/{bin_number}", timeout=5, verify=False)
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
    log_action('IP_CHECK', ip)
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10, verify=False)
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
    log_action('SITE_CHECK', url)
    
    if not url.startswith('http'):
        url = 'http://' + url
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10, allow_redirects=True, verify=False)
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
# КОМАНДА /stats (ПЕРСОНАЛЬНАЯ СТАТИСТИКА)
# ================================================

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    user_id = message.from_user.id
    stats, user_stats = get_user_stats(user_id)
    
    stats_text = (
        f"📊 *ТВОЯ СТАТИСТИКА*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Всего проверок: {user_stats['total_checks']}\n"
        f"📱 Телефонов: {user_stats['phone_checks']}\n"
        f"📧 Email: {user_stats['email_checks']}\n"
        f"💳 Карт: {user_stats['card_checks']}\n"
        f"🌐 IP: {user_stats['ip_checks']}\n"
        f"🌍 Сайтов: {user_stats['site_checks']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )
    bot.reply_to(message, stats_text, parse_mode='Markdown')

# ================================================
# КОМАНДЫ
# ================================================

@bot.message_handler(commands=['start', 'help'])
def help_cmd(message):
    bot.reply_to(message, 
        "🔍 *БОТ-ПРОВЕРЩИК v5.1*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📌 *КОМАНДЫ:*\n"
        "📱 `/phone +79229244035` — проверка телефона\n"
        "📧 `/email test@mail.com` — проверка email\n"
        "🌐 `/ip 8.8.8.8` — информация по IP\n"
        "💳 `/card 4111111111111111` — проверка карты\n"
        "🌍 `/site google.com` — проверка сайта\n"
        "📊 `/stats` — твоя статистика\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Персональная статистика сохраняется!\n"
        "✅ Локальная база операторов!\n"
        "✅ Логирование ошибок в Telegram!",
        parse_mode='Markdown')

@bot.message_handler(commands=['phone'])
def phone_cmd(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "❌ /phone +79229244035")
            return
        user_id = message.from_user.id
        update_user_stats(user_id, 'phone')
        bot.reply_to(message, check_phone(' '.join(args[1:])), parse_mode='Markdown')
    except Exception as e:
        send_log(f"Ошибка в phone_cmd: {e}")
        b
