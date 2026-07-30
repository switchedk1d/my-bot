import telebot
import requests
import re
import json
import os
import time
import socket
import ssl
import smtplib
import dns.resolver
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import whois
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================================================================
# НАСТРОЙКИ
# ================================================================
BOT_TOKEN = '8731103715:AAENjKYBq8rN7dwVU8gLKBz-X_ixIAmazdY'
PHONE_API_KEY = 'ok_7f681d2b7d574e4e5d8185bf5df6ba57'
ADMIN_ID = 6482365079

IPQS_KEY = 'wAqwCtriEodmMTT92ERWYggHKJllfjf'
ABUSEIPDB_KEY = 'fa4eaac39bf03569bdccde0d10d1a1da8c611afc4a93dd6d2c1fe91d30f56ee84b28575a327aed1c'
VT_KEY = 'be43b5c3973f77fe225d0d4a7cf4659d91e94b5c854ec1038576d67be0856640'
GREIP_KEY = '18fc1da8b62d9b5bd04123f7b2baf993'
# ================================================================

def check_phone_super(phone):
    clean = re.sub(r'[^0-9]', '', phone.strip())
    formatted = '+' + clean if not clean.startswith('+') else phone
    
    result = {
        'phone': phone,
        'clean': clean,
        'formatted': formatted,
        'valid': False,
        'country': 'Неизвестно',
        'country_code': 'Неизвестно',
        'operator': 'Неизвестно',
        'line_type': 'Неизвестно',
        'location': 'Неизвестно',
        'timezone': 'Неизвестно',
        'is_mobile': False,
        'is_voip': False,
        'is_landline': False,
        'is_fake': False,
        'is_active': 'Неизвестно',
        'fraud_score': 0,
        'is_spam': False,
        'breaches': [],
        'carrier_info': 'Неизвестно',
        'region': 'Неизвестно',
        'coordinates': 'Неизвестно',
        'sources': [],
        'suggestions': []
    }
    
    try:
        parsed = phonenumbers.parse(clean, None)
        if phonenumbers.is_valid_number(parsed):
            result['valid'] = True
            result['country'] = geocoder.country_name_for_number(parsed, 'ru')
            result['location'] = geocoder.description_for_number(parsed, 'ru')
            result['operator'] = carrier.name_for_number(parsed, 'ru')
            result['timezone'] = ', '.join(timezone.time_zones_for_number(parsed))
            result['is_mobile'] = phonenumbers.number_type(parsed) in [phonenumbers.PhoneNumberType.MOBILE, phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE]
            result['is_landline'] = phonenumbers.number_type(parsed) == phonenumbers.PhoneNumberType.FIXED_LINE
            result['is_voip'] = phonenumbers.number_type(parsed) == phonenumbers.PhoneNumberType.VOIP
            result['sources'].append('phonenumbers')
    except:
        pass
    
    COUNTRY_CODES = {
        '7': 'Россия', '1': 'США/Канада', '44': 'Великобритания',
        '49': 'Германия', '33': 'Франция', '86': 'Китай',
        '91': 'Индия', '81': 'Япония', '55': 'Бразилия',
        '66': 'Таиланд', '34': 'Испания', '39': 'Италия',
        '61': 'Австралия', '82': 'Южная Корея', '31': 'Нидерланды',
        '46': 'Швеция', '41': 'Швейцария', '48': 'Польша',
        '90': 'Турция', '380': 'Украина', '375': 'Беларусь'
    }
    for code, country in COUNTRY_CODES.items():
        if clean.startswith(code):
            result['country'] = result['country'] if result['country'] != 'Неизвестно' else country
            result['country_code'] = code
            break
    
    # ==========================================
    # ТОЛЬКО OMKAR.CLOUD API
    # ==========================================
    try:
        url = f"https://carrier-lookup-api.omkar.cloud/lookup?phone={formatted}"
        headers = {'API-Key': PHONE_API_KEY}
        response = requests.get(url, headers=headers, timeout=8, verify=False)
        data = response.json()
        if data.get('is_valid_number', False):
            result['valid'] = True
            result['carrier_info'] = data.get('carrier', 'Неизвестно')
            result['line_type'] = data.get('line_type', 'Неизвестно')
            result['sources'].append('omkar')
        else:
            result['valid'] = False
            result['is_fake'] = True
            result['sources'].append('omkar_invalid')
    except:
        pass
    
    if IPQS_KEY:
        try:
            url = f"https://ipqualityscore.com/api/json/phone/{IPQS_KEY}/{formatted}"
            response = requests.get(url, timeout=8, verify=False)
            data = response.json()
            if data.get('success', False):
                result['fraud_score'] = data.get('fraud_score', 0)
                result['is_spam'] = data.get('spam', False)
                result['is_active'] = '✅ Активен' if data.get('active', False) else '⚠️ Не активен'
                result['sources'].append('ipqualityscore')
        except:
            pass
    
    fake_patterns = ['1111111111', '2222222222', '3333333333', '4444444444',
                     '5555555555', '6666666666', '7777777777', '8888888888',
                     '9999999999', '0000000000', '1234567890', '0987654321']
    if clean in fake_patterns or len(set(clean)) == 1:
        result['is_fake'] = True
    
    if clean.startswith('7') and len(clean) >= 10:
        region_codes = {
            '495': 'Москва', '499': 'Москва', '812': 'Санкт-Петербург',
            '831': 'Нижний Новгород', '843': 'Казань', '846': 'Самара',
            '863': 'Ростов-на-Дону', '343': 'Екатеринбург', '383': 'Новосибирск'
        }
        for code, region in region_codes.items():
            if clean[1:4] == code or clean[1:4] == code[:3]:
                result['region'] = region
                break
    
    if result['valid'] and not result['is_fake']:
        status_icon = "✅"
        status_text = "ВАЛИДНЫЙ (РЕАЛЬНЫЙ)"
    elif result['is_fake']:
        status_icon = "❌"
        status_text = "ФЕЙКОВЫЙ / ТЕСТОВЫЙ"
    else:
        status_icon = "⚠️"
        status_text = "НЕ УДАЛОСЬ ПРОВЕРИТЬ"
    
    if result['is_mobile']:
        type_text = "📱 Мобильный"
    elif result['is_voip']:
        type_text = "🎧 VOIP (Виртуальный)"
    elif result['is_landline']:
        type_text = "☎️ Стационарный"
    else:
        type_text = "❓ Неизвестно"
    
    if result['fraud_score'] >= 80:
        risk_text = "🔴 ВЫСОКИЙ РИСК"
    elif result['fraud_score'] >= 50:
        risk_text = "🟡 СРЕДНИЙ РИСК"
    else:
        risk_text = "🟢 НИЗКИЙ РИСК"
    
    breaches_text = "\n".join([f"   • {b}" for b in result['breaches']]) if result['breaches'] else "   • Не найдено"
    
    return (
        f"📱 *СУПЕР-ПРОВЕРКА НОМЕРА*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_icon} *Статус:* {status_text}\n"
        f"📞 *Номер:* `{formatted}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 *Страна:* {result['country']}\n"
        f"🌐 *Код:* +{result['country_code']}\n"
        f"📍 *Регион:* {result['region']}\n"
        f"🗺️ *Координаты:* {result['coordinates']}\n"
        f"🕐 *Часовой пояс:* {result['timezone']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Оператор:* {result['operator']}\n"
        f"🏢 *Carrier:* {result['carrier_info']}\n"
        f"🔢 *Тип:* {type_text} ({result['line_type']})\n"
        f"📊 *Активность:* {result['is_active']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Оценка риска:* {risk_text} ({result['fraud_score']}/100)\n"
        f"📮 *Спам:* {'✅ Да' if result['is_spam'] else '❌ Нет'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔓 *Утечки данных:*\n{breaches_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 2. СУПЕР-ПРОВЕРКА EMAIL
# ================================================================

def check_email_super(email):
    result = {
        'email': email,
        'domain': email.split('@')[1].lower() if '@' in email else '',
        'valid_format': False,
        'domain_exists': False,
        'mx_exists': False,
        'smtp_status': 'Неизвестно',
        'is_disposable': False,
        'is_role': False,
        'is_fake': False,
        'fraud_score': 0,
        'age': 'Неизвестно',
        'registrar': 'Неизвестно',
        'breaches': [],
        'sources': []
    }
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        result['valid_format'] = True
        result['sources'].append('format')
    
    try:
        socket.gethostbyname(result['domain'])
        result['domain_exists'] = True
        result['sources'].append('dns')
    except:
        pass
    
    try:
        records = dns.resolver.resolve(result['domain'], 'MX')
        if records:
            result['mx_exists'] = True
            result['sources'].append('mx')
    except:
        pass
    
    if result['mx_exists']:
        try:
            mx_record = str(dns.resolver.resolve(result['domain'], 'MX')[0].exchange)
            server = smtplib.SMTP(timeout=10)
            server.connect(mx_record)
            server.helo()
            server.mail('test@test.com')
            code, message = server.rcpt(email)
            server.quit()
            if code == 250:
                result['smtp_status'] = '✅ Существует'
                result['sources'].append('smtp')
            else:
                result['smtp_status'] = '⚠️ Ящик не найден'
        except:
            result['smtp_status'] = '⚠️ Ошибка SMTP'
    
    try:
        w = whois.whois(result['domain'])
        if w.creation_date:
            result['age'] = (datetime.now() - w.creation_date[0]).days if isinstance(w.creation_date, list) else (datetime.now() - w.creation_date).days
            result['registrar'] = w.registrar if w.registrar else 'Неизвестно'
            result['sources'].append('whois')
    except:
        pass
    
    disposable_domains = ['tempmail.com', '10minutemail.com', 'mailinator.com', 'yopmail.com']
    if result['domain'] in disposable_domains:
        result['is_disposable'] = True
        result['sources'].append('disposable')
    
    role_patterns = ['admin', 'info', 'support', 'sales', 'contact', 'help', 'abuse', 'postmaster']
    if email.split('@')[0].lower() in role_patterns:
        result['is_role'] = True
        result['sources'].append('role')
    
    if IPQS_KEY:
        try:
            url = f"https://ipqualityscore.com/api/json/email/{IPQS_KEY}/{email}"
            response = requests.get(url, timeout=8, verify=False)
            data = response.json()
            if data.get('success', False):
                result['fraud_score'] = data.get('fraud_score', 0)
                result['is_fake'] = data.get('disposable', False) or data.get('honeypot', False)
                result['sources'].append('ipqualityscore')
        except:
            pass
    
    if result['valid_format'] and result['mx_exists'] and result['smtp_status'] == '✅ Существует':
        status_icon = "✅"
        status_text = "ВАЛИДНЫЙ (РЕАЛЬНЫЙ)"
    elif result['valid_format'] and result['domain_exists'] and result['mx_exists']:
        status_icon = "⚠️"
        status_text = "ФОРМАТ И ДОМЕН ВЕРНЫ, НО ПОЧТА НЕ ПРОВЕРЕНА"
    elif result['valid_format']:
        status_icon = "⚠️"
        status_text = "ФОРМАТ ВЕРЕН, НО ДОМЕН НЕ СУЩЕСТВУЕТ"
    else:
        status_icon = "❌"
        status_text = "НЕВАЛИДНЫЙ ФОРМАТ"
    
    if result['fraud_score'] >= 80:
        risk_text = "🔴 ВЫСОКИЙ РИСК"
    elif result['fraud_score'] >= 50:
        risk_text = "🟡 СРЕДНИЙ РИСК"
    else:
        risk_text = "🟢 НИЗКИЙ РИСК"
    
    if result['age'] != 'Неизвестно':
        age_text = f"{result['age']} дней" if result['age'] < 365 else f"{result['age'] // 365} лет"
    else:
        age_text = "Неизвестно"
    
    breaches_text = "\n".join([f"   • {b}" for b in result['breaches']]) if result['breaches'] else "   • Не найдено"
    
    return (
        f"📧 *СУПЕР-ПРОВЕРКА EMAIL*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_icon} *Статус:* {status_text}\n"
        f"📧 *Email:* `{email}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 *Домен:* {result['domain']}\n"
        f"📡 *MX-записи:* {'✅ Есть' if result['mx_exists'] else '❌ Нет'}\n"
        f"📬 *SMTP-проверка:* {result['smtp_status']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🗑️ *Временная почта:* {'✅ Да' if result['is_disposable'] else '❌ Нет'}\n"
        f"👔 *Ролевой email:* {'✅ Да' if result['is_role'] else '❌ Нет'}\n"
        f"📅 *Возраст домена:* {age_text}\n"
        f"👤 *Регистратор:* {result['registrar']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Оценка риска:* {risk_text} ({result['fraud_score']}/100)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔓 *Утечки данных:*\n{breaches_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 3. СУПЕР-ПРОВЕРКА КАРТЫ
# ================================================================

def check_card_super(card):
    clean = re.sub(r'[\s\-]', '', card.strip())
    result = {
        'card': card,
        'clean': clean,
        'formatted': f"{clean[:4]} {clean[4:8]} {clean[8:12]} {clean[12:16]}" if len(clean) >= 16 else clean,
        'valid_luhn': False,
        'system': 'Неизвестно',
        'bank': 'Неизвестно',
        'country': 'Неизвестно',
        'sources': []
    }
    
    if len(clean) not in [15, 16]:
        return "❌ Невалидная длина карты"
    
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
        return "❌ Невалидная карта (ошибка алгоритма Луна)"
    
    first = clean[0]
    if first == '4':
        result['system'] = 'VISA'
    elif first == '5':
        result['system'] = 'MasterCard'
    elif first == '3' and clean[1] in '47':
        result['system'] = 'American Express'
    elif first == '3':
        result['system'] = 'JCB'
    elif first == '6':
        result['system'] = 'Discover'
    else:
        result['system'] = 'Неизвестно'
    
    try:
        url = f"https://binlist.net/json/{clean[:6]}"
        response = requests.get(url, timeout=5, verify=False)
        data = response.json()
        if data.get('bank'):
            result['bank'] = data['bank'].get('name', 'Неизвестно')
            result['country'] = data.get('country', {}).get('name', 'Неизвестно')
            result['sources'].append('binlist')
    except:
        pass
    
    return (
        f"💳 *СУПЕР-ПРОВЕРКА КАРТЫ*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Статус:* ВАЛИДНАЯ\n"
        f"💳 *Номер:* `{result['formatted']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 *Банк:* {result['bank']}\n"
        f"🌍 *Страна:* {result['country']}\n"
        f"💳 *Система:* {result['system']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 4. СУПЕР-ПРОВЕРКА IP
# ================================================================

def check_ip_super(ip):
    result = {
        'ip': ip,
        'country': 'Неизвестно',
        'country_code': 'Неизвестно',
        'city': 'Неизвестно',
        'isp': 'Неизвестно',
        'proxy': False,
        'vpn': False,
        'tor': False,
        'abuse_score': 0,
        'sources': []
    }
    
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=8, verify=False)
        data = response.json()
        if data.get('status') == 'success':
            result['country'] = data.get('country', 'Неизвестно')
            result['country_code'] = data.get('countryCode', 'Неизвестно')
            result['city'] = data.get('city', 'Неизвестно')
            result['isp'] = data.get('isp', 'Неизвестно')
            result['sources'].append('ip-api')
    except:
        pass
    
    if IPQS_KEY:
        try:
            url = f"https://ipqualityscore.com/api/json/ip/{IPQS_KEY}/{ip}"
            response = requests.get(url, timeout=8, verify=False)
            data = response.json()
            if data.get('success', False):
                result['proxy'] = data.get('proxy', False)
                result['vpn'] = data.get('vpn', False)
                result['tor'] = data.get('tor', False)
                result['abuse_score'] = data.get('fraud_score', 0)
                result['sources'].append('ipqualityscore')
        except:
            pass
    
    if ABUSEIPDB_KEY:
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {'Key': ABUSEIPDB_KEY, 'Accept': 'application/json'}
            params = {'ipAddress': ip, 'maxAgeInDays': 90}
            response = requests.get(url, headers=headers, params=params, timeout=8, verify=False)
            if response.status_code == 200:
                result['sources'].append('abuseipdb')
        except:
            pass
    
    privacy_text = "🔒 АНОНИМНЫЙ" if (result['proxy'] or result['vpn'] or result['tor']) else "🌐 ОТКРЫТЫЙ"
    
    return (
        f"🌐 *СУПЕР-ПРОВЕРКА IP*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *IP:* `{ip}`\n"
        f"🔒 *Статус:* {privacy_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 *Страна:* {result['country']} ({result['country_code']})\n"
        f"🏙️ *Город:* {result['city']}\n"
        f"📡 *Провайдер:* {result['isp']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *VPN:* {'✅ Да' if result['vpn'] else '❌ Нет'}\n"
        f"🌐 *Proxy:* {'✅ Да' if result['proxy'] else '❌ Нет'}\n"
        f"🧅 *Tor:* {'✅ Да' if result['tor'] else '❌ Нет'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Оценка риска:* {result['abuse_score']}/100\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 5. СУПЕР-ПРОВЕРКА САЙТА
# ================================================================

def check_site_super(url):
    if not url.startswith('http'):
        url = 'http://' + url
    
    domain = re.sub(r'^https?://', '', url).split('/')[0]
    result = {
        'url': url,
        'domain': domain,
        'status': 'Неизвестно',
        'status_code': 'Неизвестно',
        'ssl_valid': False,
        'ssl_expiry': 'Неизвестно',
        'whois_created': 'Неизвестно',
        'registrar': 'Неизвестно',
        'is_malicious': False,
        'sources': []
    }
    
    try:
        start = time.time()
        response = requests.get(url, timeout=10, allow_redirects=True, verify=False)
        result['status'] = 'Доступен'
        result['status_code'] = response.status_code
        result['sources'].append('requests')
    except:
        result['status'] = 'Недоступен'
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                result['ssl_valid'] = True
                result['ssl_expiry'] = cert['notAfter']
                result['sources'].append('ssl')
    except:
        pass
    
    try:
        w = whois.whois(domain)
        if w.creation_date:
            result['whois_created'] = str(w.creation_date)
         result['registrar'] = w.registrar if w.registrar else 'Неизвестно'
            result['sources'].append('whois')
    except:
        pass
    
    if VT_KEY:
        try:
            vt_url = f"https://www.virustotal.com/api/v3/domains/{domain}"
            headers = {'x-apikey': VT_KEY}
            response = requests.get(vt_url, headers=headers, timeout=8, verify=False)
            data = response.json()
            if data.get('data'):
                malicious = data['data']['attributes'].get('last_analysis_stats', {}).get('malicious', 0)
                result['is_malicious'] = malicious > 0
                result['sources'].append('virustotal')
        except:
            pass
    
    return (
        f"🌍 *СУПЕР-ПРОВЕРКА САЙТА*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ *Статус:* {result['status']}\n"
        f"🌐 *URL:* `{url}`\n"
        f"📊 *Код ответа:* {result['status_code']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 *SSL:* {'✅ Действителен' if result['ssl_valid'] else '❌ Нет SSL'}\n"
        f"📅 *Истекает:* {result['ssl_expiry']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 *WHOIS создан:* {result['whois_created']}\n"
        f"👤 *Регистратор:* {result['registrar']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Вредоносность:* {'🔴 ДА' if result['is_malicious'] else '🟢 НЕТ'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# БОТ
# ================================================================
bot = telebot.TeleBot(BOT_TOKEN)

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

def get_stats(user_id):
    stats = load_stats()
    uid = str(user_id)
    if uid not in stats:
        stats[uid] = {'total': 0, 'phone': 0, 'email': 0, 'card': 0, 'ip': 0, 'site': 0}
    return stats, stats[uid]

def update_stats(user_id, check_type):
    stats = load_stats()
    uid = str(user_id)
    if uid not in stats:
        stats[uid] = {'total': 0, 'phone': 0, 'email': 0, 'card': 0, 'ip': 0, 'site': 0}
    stats[uid]['total'] += 1
    stats[uid][check_type] += 1
    save_stats(stats)

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📱 Номер", callback_data="phone"),
        InlineKeyboardButton("📧 Email", callback_data="email"),
        InlineKeyboardButton("💳 Карта", callback_data="card"),
        InlineKeyboardButton("🌐 IP", callback_data="ip"),
        InlineKeyboardButton("🌍 Сайт", callback_data="site"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        InlineKeyboardButton("📋 Помощь", callback_data="help")
    )
    return kb

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "🔍 *switchprob @hinewrock*\n\n👇 Выбери действие:",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if call.data == "stats":
        uid = call.from_user.id
        stats, user_stats = get_stats(uid)
        bot.edit_message_text(
            f"📊 *СТАТИСТИКА*\n━━━━━━━━━━━━━━━━━━━━━━\n📱 Всего: {user_stats['total']}\n📱 Телефонов: {user_stats['phone']}\n📧 Email: {user_stats['email']}\n💳 Карт: {user_stats['card']}\n🌐 IP: {user_stats['ip']}\n🌍 Сайтов: {user_stats['site']}",
            chat_id, msg_id, parse_mode='Markdown'
        )
        return
    
    if call.data == "help":
        bot.edit_message_text(
            "📋 *ПОМОЩЬ*\n━━━━━━━━━━━━━━━━━━━━━━\n📱 Номер — оператор, страна\n📧 Email — валидность\n💳 Карта — платёжная система\n🌐 IP — страна, город\n🌍 Сайт — статус\n━━━━━━━━━━━━━━━━━━━━━━\n👤 @switchprob",
            chat_id, msg_id, parse_mode='Markdown'
        )
        return
    
    bot.edit_message_text(
        f"📝 *ВВЕДИ ДАННЫЕ ДЛЯ {call.data.upper()}*",
        chat_id, msg_id, parse_mode='Markdown'
    )
    
    if call.data == "phone":
        bot.register_next_step_handler(call.message, process_phone)
    elif call.data == "email":
        bot.register_next_step_handler(call.message, process_email)
    elif call.data == "card":
        bot.register_next_step_handler(call.message, process_card)
    elif call.data == "ip":
        bot.register_next_step_handler(call.message, process_ip)
    elif call.data == "site":
        bot.register_next_step_handler(call.message, process_site)

def process_phone(message):
    uid = message.from_user.id
    result = check_phone_super(message.text)
    update_stats(uid, 'phone')
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())

def process_email(message):
    uid = message.from_user.id
    result = check_email_super(message.text)
    update_stats(uid, 'email')
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())

def process_card(message):
    uid = message.from_user.id
    result = check_card_super(message.text)
    update_stats(uid, 'card')
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())

def process_ip(message):
    uid = message.from_user.id
    result = check_ip_super(message.text)
    update_stats(uid, 'ip')
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())

def process_site(message):
    uid = message.from_user.id
    result = check_site_super(message.text)
    update_stats(uid, 'site')
    bot.send_message(message.chat.id, result, parse_mode='Markdown', reply_markup=main_menu())

# ================================================================
# ЗАПУСК
# ================================================================

print("=" * 60)
print("  🤖 switchprob @hinewrock")
print("=" * 60)
print("✅ Супер-проверки активны!")
print("📌 Телефон, Email, Карта, IP, Сайт")
print("=" * 60)

if __name__ == "__main__":
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"❌ Бот упал: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)
    
         
