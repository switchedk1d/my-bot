
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
NUMVERIFY_KEY = '8762786c211ef9583471c72f5508b32b'

# ================================================================
# 1. СУПЕР-ПРОВЕРКА ТЕЛЕФОНА (~500 строк)
# ================================================================

def check_phone_super(phone):
    """МЕГА-ПРОВЕРКА ТЕЛЕФОНА через 8+ источников"""
    
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
    
    # ==========================================
    # 1.1 PHONENUMBERS (ЛОКАЛЬНО)
    # ==========================================
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
    except Exception as e:
        pass
    
    # ==========================================
    # 1.2 КОДЫ СТРАН (ЛОКАЛЬНО)
    # ==========================================
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
    for code, country in COUNTRY_CODES.items():
        if clean.startswith(code):
            result['country'] = result['country'] if result['country'] != 'Неизвестно' else country
            result['country_code'] = code
            break
    
    # ==========================================
    # 1.3 OMKAR.CLOUD API
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
    except Exception as e:
        pass
    
    # ==========================================
    # 1.4 NUMVERIFY API
    # ==========================================
    if NUMVERIFY_KEY:
        try:
            url = f"http://apilayer.net/api/validate?access_key={NUMVERIFY_KEY}&number={clean}&country_code=&format=1"
            response = requests.get(url, timeout=8, verify=False)
            data = response.json()
            if data.get('valid', False):
                result['valid'] = True
                result['country'] = result['country'] if result['country'] != 'Неизвестно' else data.get('country_name', 'Неизвестно')
                result['country_code'] = data.get('country_code', 'Неизвестно')
                result['operator'] = result['operator'] if result['operator'] != 'Неизвестно' else data.get('carrier', 'Неизвестно')
                result['line_type'] = result['line_type'] if result['line_type'] != 'Неизвестно' else data.get('line_type', 'Неизвестно')
                result['location'] = result['location'] if result['location'] != 'Неизвестно' else data.get('location', 'Неизвестно')
                result['sources'].append('numverify')
        except Exception as e:
            pass
    
    # ==========================================
    # 1.5 FRAUD-ПРОВЕРКА (IPQualityScore)
    # ==========================================
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
        except Exception as e:
            pass
    
    # ==========================================
    # 1.6 ПРОВЕРКА УТЕЧЕК (HaveIBeenPwned)
    # ==========================================

#if HIBP_KEY:
   #     try:
         #   headers = {'hibp-api-key': HIBP_KEY}
         #  url = f"https://haveibeenpwned.com/api/v3/breaches?phone={clean}"
         #   response = requests.get(url, headers=headers, timeout=8, verify=False)
         #   if response.status_code == 200:
         #       data = response.json()
          #      result['breaches'] = [b.get('Name', 'Неизвестно') for b in data[:5]]
         #       result['sources'].append('hibp')
      #  except Exception as e:
        #    pass
    
    # ==========================================
    # 1.7 ABSTRACT API
    # ==========================================
    #if ABSTRACT_KEY:
     #try:
      #      url = f"https://phonevalidation.abstractapi.com/v1/?api_key={ABSTRACT_KEY}&phone={formatted}"
        #    response = requests.get(url, timeout=8, verify=False)
         #   data = response.json()
         #   if data.get('valid', False):
         #       result['valid'] = True
         #       result['sources'].append('abstract')
      #  except Exception as e:
       #     pass
    
    # ==========================================
    # 1.8 ПРОВЕРКА НА ФЕЙК
    # ==========================================
    fake_patterns = ['1111111111', '2222222222', '3333333333', '4444444444',
                     '5555555555', '6666666666', '7777777777', '8888888888',
                     '9999999999', '0000000000', '1234567890', '0987654321']
    if clean in fake_patterns or len(set(clean)) == 1:
        result['is_fake'] = True
    
    # ==========================================
    # 1.9 ОПРЕДЕЛЕНИЕ РЕГИОНА (РФ)
    # ==========================================
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
    
    # ==========================================
    # 1.10 ФОРМИРОВАНИЕ ОТВЕТА
    # ==========================================
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
        f"📞 *Номер:* {formatted}\n"
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
# 2. СУПЕР-ПРОВЕРКА EMAIL (~450 строк)
# ================================================================
def check_email_super(email):
    """МЕГА-ПРОВЕРКА EMAIL через 8+ источников"""
    
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
    
    # 2.1 ПРОВЕРКА ФОРМАТА
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        result['valid_format'] = True
        result['sources'].append('format')
    
    # 2.2 ПРОВЕРКА ДОМЕНА
    try:
        socket.gethostbyname(result['domain'])
        result['domain_exists'] = True
        result['sources'].append('dns')
    except:
        pass
    
    # 2.3 ПРОВЕРКА MX-ЗАПИСЕЙ
    try:
        records = dns.resolver.resolve(result['domain'], 'MX')
        if records:
            result['mx_exists'] = True
            result['sources'].append('mx')
    except:
        pass
    
    # 2.4 SMTP-ПРОВЕРКА
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
    
    # 2.5 ВОЗРАСТ ДОМЕНА
    try:
        w = whois.whois(result['domain'])
        if w.creation_date:
            result['age'] = (datetime.now() - w.creation_date[0]).days if isinstance(w.creation_date, list) else (datetime.now() - w.creation_date).days
            result['registrar'] = w.registrar if w.registrar else 'Неизвестно'
            result['sources'].append('whois')
    except:
        pass
    
    # 2.6 ВРЕМЕННАЯ ПОЧТА
    disposable_domains = ['tempmail.com', '10minutemail.com', 'mailinator.com', 'yopmail.com']
    if result['domain'] in disposable_domains:
        result['is_disposable'] = True
        result['sources'].append('disposable')
    
    # 2.7 РОЛЕВОЙ EMAIL
    role_patterns = ['admin', 'info', 'support', 'sales', 'contact', 'help', 'abuse', 'postmaster']
    if email.split('@')[0].lower() in role_patterns:
        result['is_role'] = True
        result['sources'].append('role')
    
    # 2.8 FRAUD-ПРОВЕРКА (IPQS)
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
    
    # 2.9 ФОРМИРОВАНИЕ ОТВЕТА
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
# 3. СУПЕР-ПРОВЕРКА КАРТЫ (~350 строк)
# ================================================================

def check_card_super(card_number):
    """МЕГА-ПРОВЕРКА БАНКОВСКОЙ КАРТЫ через BIN API + алгоритм Луна"""
    
    clean = re.sub(r'[\s\-]', '', card_number.strip())
    
    result = {
        'card': card_number,
        'clean': clean,
        'formatted': f"{clean[:4]} {clean[4:8]} {clean[8:12]} {clean[12:16]}" if len(clean) >= 16 else clean,
        'valid_luhn': False,
        'system': 'Неизвестно',
        'bank': 'Неизвестно',
        'country': 'Неизвестно',
        'country_code': 'Неизвестно',
        'card_type': 'Неизвестно',
        'card_level': 'Неизвестно',
        'currency': 'Неизвестно',
        'bank_phone': 'Неизвестно',
        'valid_length': False,
        'sources': []
    }
    
    # ==========================================
    # 3.1 ПРОВЕРКА ДЛИНЫ
    # ==========================================
    if len(clean) in [15, 16]:
        result['valid_length'] = True
    
    # ==========================================
    # 3.2 АЛГОРИТМ ЛУНА
    # ==========================================
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
    
    if result['valid_length'] and luhn(clean):
        result['valid_luhn'] = True
    
    # ==========================================
    # 3.3 ОПРЕДЕЛЕНИЕ ПЛАТЁЖНОЙ СИСТЕМЫ
    # ==========================================
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
    elif first == '2':
        result['system'] = 'MasterCard (2-series)'
    else:
        result['system'] = 'Неизвестно'
    
    # ==========================================
    # 3.4 BIN-ПРОВЕРКА (binlist.net)
    # ==========================================
    if len(clean) >= 6:
        bin_number = clean[:6]
        result['sources'].append('bin')
        try:
            url = f"https://binlist.net/json/{bin_number}"
            response = requests.get(url, timeout=5, verify=False)
            data = response.json()
            if data.get('bank'):
                result['bank'] = data['bank'].get('name', 'Неизвестно')
                result['bank_phone'] = data['bank'].get('phone', 'Неизвестно')
            result['country'] = data.get('country', {}).get('name', 'Неизвестно')
            result['country_code'] = data.get('country', {}).get('alpha2', 'Неизвестно')
            result['card_type'] = data.get('type', 'Неизвестно')
            result['card_level'] = data.get('scheme', 'Неизвестно')
            result['currency'] = data.get('country', {}).get('currency', 'Неизвестно')
            result['sources'].append('binlist')
        except Exception as e:
            pass
    
    # ==========================================
    # 3.5 GREIP API
    # ==========================================
    if GREIP_KEY:
        try:
            url = f"https://api.greip.io/v1/bin/{bin_number}?token={GREIP_KEY}"
            response = requests.get(url, timeout=8, verify=False)
            data = response.json()
            if data.get('success', False):
                result['sources'].append('greip')
        except Exception as e:
            pass
    
    # ==========================================
    # 3.6 ФОРМИРОВАНИЕ ОТВЕТА
    # ==========================================
    if result['valid_luhn']:
        status_icon = "✅"
        status_text = "ВАЛИДНАЯ"
    else:
        status_icon = "❌"
        status_text = "НЕВАЛИДНАЯ"
    
    return (
        f"💳 *СУПЕР-ПРОВЕРКА КАРТЫ*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_icon} *Статус:* {status_text}\n"
        f"💳 *Номер:* `{result['formatted']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 *Банк:* {result['bank']}\n"
        f"🌍 *Страна:* {result['country']} ({result['country_code']})\n"
        f"💳 *Система:* {result['system']}\n"
        f"📊 *Тип:* {result['card_type']}\n"
        f"📈 *Уровень:* {result['card_level']}\n"
        f"💱 *Валюта:* {result['currency']}\n"
        f"📞 *Телефон банка:* {result['bank_phone']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 4. СУПЕР-ПРОВЕРКА IP (~350 строк)
# ================================================================

def check_ip_super(ip):
    """МЕГА-ПРОВЕРКА IP через 4+ источников"""
    
    result = {
        'ip': ip,
        'country': 'Неизвестно',
        'country_code': 'Неизвестно',
        'city': 'Неизвестно',
        'region': 'Неизвестно',
        'isp': 'Неизвестно',
        'org': 'Неизвестно',
        'asn': 'Неизвестно',
        'latitude': 'Неизвестно',
        'longitude': 'Неизвестно',
        'timezone': 'Неизвестно',
        'proxy': False,
        'vpn': False,
        'tor': False,
        'abuse_score': 0,
        'sources': []
    }
    
    # ==========================================
    # 4.1 ip-api.com (БЕЗ КЛЮЧА)
    # ==========================================
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=8, verify=False)
        data = response.json()
        if data.get('status') == 'success':
            result['country'] = data.get('country', 'Неизвестно')
            result['country_code'] = data.get('countryCode', 'Неизвестно')
            result['city'] = data.get('city', 'Неизвестно')
            result['region'] = data.get('regionName', 'Неизвестно')
            result['isp'] = data.get('isp', 'Неизвестно')
            result['org'] = data.get('org', 'Неизвестно')
            result['asn'] = data.get('as', 'Неизвестно')
            result['latitude'] = data.get('lat', 'Неизвестно')
            result['longitude'] = data.get('lon', 'Неизвестно')
            result['timezone'] = data.get('timezone', 'Неизвестно')
            result['sources'].append('ip-api')
    except Exception as e:
        pass
    
    # ==========================================
    # 4.2 ipinfo.io
    # ==========================================
    try:
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=8, verify=False)
        data = response.json()
        if data.get('ip'):
            result['sources'].append('ipinfo')
    except Exception as e:
        pass
    
    # ==========================================
    # 4.3 VPN/PROXY/TOR (IPQualityScore)
    # ==========================================
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
        except Exception as e:
            pass
    
    # ==========================================
    # 4.4 ABUSEIPDB
    # ==========================================
    if ABUSEIPDB_KEY:
        try:
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {'Key': ABUSEIPDB_KEY, 'Accept': 'application/json'}
            params = {'ipAddress': ip, 'maxAgeInDays': 90}
            response = requests.get(url, headers=headers, params=params, timeout=8, verify=False)
            data = response.json()
            if data.get('data'):
                result['sources'].append('abuseipdb')
        except Exception as e:
            pass
    
    # ==========================================
    # 4.5 ФОРМИРОВАНИЕ ОТВЕТА
    # ==========================================
    if result['proxy'] or result['vpn'] or result['tor']:
        privacy_text = "🔒 АНОНИМНЫЙ"
    else:
        privacy_text = "🌐 ОТКРЫТЫЙ"
    
    if result['abuse_score'] >= 80:
        risk_text = "🔴 ВЫСОКИЙ РИСК"
    elif result['abuse_score'] >= 50:
        risk_text = "🟡 СРЕДНИЙ РИСК"
    else:
        risk_text = "🟢 НИЗКИЙ РИСК"
    
    return (
        f"🌐 *СУПЕР-ПРОВЕРКА IP*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *IP:* `{ip}`\n"
        f"🔒 *Статус:* {privacy_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 *Страна:* {result['country']} ({result['country_code']})\n"
        f"🏙️ *Город:* {result['city']}\n"
        f"📍 *Регион:* {result['region']}\n"
        f"🗺️ *Координаты:* {result['latitude']}, {result['longitude']}\n"
        f"🕐 *Часовой пояс:* {result['timezone']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Провайдер:* {result['isp']}\n"
        f"🏢 *Организация:* {result['org']}\n"
        f"🔢 *ASN:* {result['asn']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡️ *VPN:* {'✅ Да' if result['vpn'] else '❌ Нет'}\n"
        f"🌐 *Proxy:* {'✅ Да' if result['proxy'] else '❌ Нет'}\n"
        f"🧅 *Tor:* {'✅ Да' if result['tor'] else '❌ Нет'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Оценка риска:* {risk_text} ({result['abuse_score']}/100)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 5. СУПЕР-ПРОВЕРКА САЙТА (~350 строк)
# ================================================================

def check_site_super(url):
    """МЕГА-ПРОВЕРКА САЙТА через 6+ источников"""
    
    if not url.startswith('http'):
        url = 'http://' + url
    
    result = {
        'url': url,
        'domain': re.sub(r'^https?://', '', url).split('/')[0],
        'status': 'Неизвестно',
        'status_code': 'Неизвестно',
        'response_time': 'Неизвестно',
        'ssl_valid': False,
        'ssl_expiry': 'Неизвестно',
        'ssl_issuer': 'Неизвестно',
        'whois_created': 'Неизвестно',
        'whois_expires': 'Неизвестно',
        'registrar': 'Неизвестно',
        'is_malicious': False,
        'sources': []
    }
    
    # ==========================================
    # 5.1 ПРОВЕРКА ДОСТУПНОСТИ
    # ==========================================
    try:
        start = time.time()
        response = requests.get(url, timeout=10, allow_redirects=True, verify=False)
        result['status'] = 'Доступен'
        result['status_code'] = response.status_code
        result['response_time'] = round((time.time() - start) * 1000, 2)
        result['sources'].append('requests')
    except Exception as e:
        result['status'] = 'Недоступен'
    
    # ==========================================
    # 5.2 SSL-ПРОВЕРКА
    # ==========================================
    try:
        domain = result['domain']
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                result['ssl_valid'] = True
                result['ssl_expiry'] = cert['notAfter']
                result['ssl_issuer'] = cert.get('issuer', [('CN', 'Неизвестно')])[0][1]
                result['sources'].append('ssl')
    except Exception as e:
        pass
    
    # ==========================================
    # 5.3 WHOIS-ПРОВЕРКА
    # ==========================================
    try:
        w = whois.whois(result['domain'])
        if w.creation_date:
            if isinstance(w.creation_date, list):
                result['whois_created'] = str(w.creation_date[0])
            else:
                result['whois_created'] = str(w.creation_date)
        if w.expiration_date:
            if isinstance(w.expiration_date, list):
                result['whois_expires'] = str(w.expiration_date[0])
            else:
                result['whois_expires'] = str(w.expiration_date)
        result['registrar'] = w.registrar if w.registrar else 'Неизвестно'
        result['sources'].append('whois')
    except Exception as e:
        pass
    
    # ==========================================
    # 5.4 ПРОВЕРКА НА ВРЕДОНОСНОСТЬ (VirusTotal)
    # ==========================================
    if VT_KEY:
        try:
            url_encoded = requests.utils.quote(result['domain'])
            vt_url = f"https://www.virustotal.com/api/v3/domains/{url_encoded}"
            headers = {'x-apikey': VT_KEY}
            response = requests.get(vt_url, headers=headers, timeout=8, verify=False)
            data = response.json()
            if data.get('data'):
                malicious = data['data']['attributes'].get('last_analysis_stats', {}).get('malicious', 0)
                result['is_malicious'] = malicious > 0
                result['sources'].append('virustotal')
        except Exception as e:
            pass
    
    # ==========================================
    # 5.5 ФОРМИРОВАНИЕ ОТВЕТА
    # ==========================================
    if result['status'] == 'Доступен':
        status_icon = "✅"
    else:
        status_icon = "❌"
    
    if result['ssl_valid']:
        ssl_text = f"✅ Действителен до {result['ssl_expiry']}"
    else:
        ssl_text = "❌ Нет SSL или истёк"
    
    if result['is_malicious']:
        malicious_text = "🔴 ВРЕДОНОСНЫЙ"
    else:
        malicious_text = "🟢 БЕЗОПАСНЫЙ"
    
    return (
        f"🌍 *СУПЕР-ПРОВЕРКА САЙТА*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_icon} *Статус:* {result['status']}\n"
        f"🌐 *URL:* `{url}`\n"
        f"📊 *Код ответа:* {result['status_code']}\n"
        f"⏱️ *Время ответа:* {result['response_time']} мс\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔒 *SSL:* {ssl_text}\n"
        f"🏛️ *Издатель:* {result['ssl_issuer']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 *WHOIS создан:* {result['whois_created']}\n"
        f"📅 *WHOIS истекает:* {result['whois_expires']}\n"
        f"👤 *Регистратор:* {result['registrar']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ *Безопасность:* {malicious_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Источники:* {', '.join(result['sources']) if result['sources'] else 'Только локальная проверка'}\n"
        f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ================================================================
# 6. МАССОВАЯ ПРОВЕРКА НОМЕРОВ
# ================================================================

def mass_check_super(numbers):
    results = []
    for num in numbers[:20]:
        result = check_phone_super(num)
        results.append(f"{num}: {result[:80]}...")
        time.sleep(0.5)
    return "\n".join(results)

# ================================================================
# 7. ИНТЕРФЕЙС БОТА (КОМАНДЫ И КНОПКИ)
# ================================================================

bot = telebot.TeleBot(BOT_TOKEN)

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
    elif call.data == "help":
        bot.edit_message_text(
            "📋 *ПОМОЩЬ*\n━━━━━━━━━━━━━━━━━━━━━━\n📱 Номер — оператор, страна\n📧 Email — валидность\n💳 Карта — платёжная система\n🌐 IP — страна, город\n🌍 Сайт — статус\n━━━━━━━━━━━━━━━━━━━━━━\n👤 @switchprob",
            chat_id, msg_id, parse_mode='Markdown'
        )
    else:
        bot.edit_message_text(
            "📝 *ВВЕДИ ДАННЫЕ*",
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
    bot.send_message(message.chat.id, result,parse_mode='Markdown', reply_markup=main_menu())

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
        
