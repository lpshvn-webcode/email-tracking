#!/usr/bin/env python3
"""
Отправка email с измененной датой (для исследования в области кибербезопасности)
Демонстрирует разницу между заголовками Date и Received
"""

import smtplib
import dns.resolver
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from datetime import datetime
import os
import sys
from pathlib import Path

# Импорт конфигурации
from config import (
    SENDER_EMAIL, RECIPIENT_EMAIL, FAKE_DATE,
    EMAIL_SUBJECT, EMAIL_BODY, ATTACHMENTS,
    SMTP_PORT, SMTP_TIMEOUT
)


def parse_fake_date(date_str):
    """
    Преобразовать строку даты в timestamp для заголовка Date
    
    Args:
        date_str: Строка даты в формате "DD.MM.YYYY HH:MM:SS"
    
    Returns:
        Строка в формате RFC 2822
    """
    try:
        # Парсим дату из формата DD.MM.YYYY HH:MM:SS
        dt = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        # Конвертируем в RFC 2822 формат для заголовка Date
        return formatdate(timeval=dt.timestamp(), localtime=True)
    except Exception as e:
        print(f"✗ Ошиб��а парсинга даты '{date_str}': {e}")
        print("  Используется текущая дата")
        return formatdate(localtime=True)


def get_mx_server(domain):
    """
    Получить адрес MX сервера для домена
    
    Args:
        domain: Доменное имя
    
    Returns:
        Адрес MX сервера или None
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        # Сортируем по приоритету и берем первый
        mx_list = [(mx.preference, str(mx.exchange).rstrip('.')) for mx in mx_records]
        mx_list.sort()
        return mx_list[0][1]
    except Exception as e:
        print(f"✗ Ошибка получения MX записи для {domain}: {e}")
        return None


def create_email_with_attachments(sender, recipient, subject, body, fake_date, attachments):
    """
    Создать email сообщение с вложениями и измененной датой
    
    Args:
        sender: Email отправителя
        recipient: Email получателя
        subject: Тема письма
        body: Текст письма
        fake_date: Дата для заголовка Date (RFC 2822 формат)
        attachments: Список путей к файлам для прикрепления
    
    Returns:
        EmailMessage объект
    """
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg['Message-ID'] = make_msgid(domain=sender.split('@')[1])
    
    # ВАЖНО: Устанавливаем подделанную дату
    msg['Date'] = fake_date
    
    # Основной текст письма
    msg.set_content(body)
    
    # Добавляем вложения
    for attachment_path in attachments:
        if not os.path.exists(attachment_path):
            print(f"⚠ Предупреждение: Файл '{attachment_path}' не найден, пропускаем")
            continue
        
        try:
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
                file_name = Path(attachment_path).name
                
                # Определяем тип содержимого
                if attachment_path.endswith('.txt'):
                    maintype = 'text'
                    subtype = 'plain'
                elif attachment_path.endswith('.pdf'):
                    maintype = 'application'
                    subtype = 'pdf'
                elif attachment_path.endswith(('.jpg', '.jpeg')):
                    maintype = 'image'
                    subtype = 'jpeg'
                elif attachment_path.endswith('.png'):
                    maintype = 'image'
                    subtype = 'png'
                else:
                    maintype = 'application'
                    subtype = 'octet-stream'
                
                msg.add_attachment(file_data, 
                                 maintype=maintype, 
                                 subtype=subtype, 
                                 filename=file_name)
                print(f"✓ Прикреплен файл: {file_name}")
        except Exception as e:
            print(f"✗ Ошибка прикрепления файла '{attachment_path}': {e}")
    
    return msg


def send_email_direct(mx_server, sender, recipient, msg):
    """
    Отправить email напрямую на MX сервер
    
    Args:
        mx_server: Адрес MX сервера
        sender: Email отправителя
        recipient: Email получателя
        msg: EmailMessage объект
    
    Returns:
        True если успешно, False если ошибка
    """
    print(f"\n📧 Отправка письма...")
    print(f"   От: {sender}")
    print(f"   Кому: {recipient}")
    print(f"   MX сервер: {mx_server}:{SMTP_PORT}")
    print(f"   Поддельная дата: {msg['Date']}")
    print("-" * 60)
    
    try:
        # Подключаемся к MX серверу
        print(f"🔌 Подключение к {mx_server}:{SMTP_PORT}...")
        with smtplib.SMTP(mx_server, SMTP_PORT, timeout=SMTP_TIMEOUT) as server:
            # Включаем режим отладки для логирования SMTP диалога
            server.set_debuglevel(1)
            
            print(f"✓ Подключено к {mx_server}")
            
            # EHLO/HELO
            server.ehlo()
            
            # Попытка использовать STARTTLS (если поддерживается)
            try:
                server.starttls()
                server.ehlo()
                print("✓ STARTTLS установлен")
            except:
                print("⚠ STARTTLS не поддерживается, продолжаем без шифрования")
            
            # Отправляем письмо
            server.send_message(msg)
            
            print("-" * 60)
            print("✓ Письмо успешно отправлено!")
            print(f"✓ Заголовок Date: {msg['Date']}")
            print(f"✓ Реальное время отправки: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            print("\n💡 Совет: При просмотре исходного текста письма сравните:")
            print("   - Заголовок 'Date:' (подделанная дата)")
            print("   - Заголовки 'Received:' (реальное время)")
            
            return True
            
    except smtplib.SMTPException as e:
        print(f"\n✗ SMTP ошибка: {e}")
        return False
    except ConnectionRefusedError:
        print(f"\n✗ Ошибка: Соединение отклонено {mx_server}:{SMTP_PORT}")
        print("  Возможные причины:")
        print("  - Порт 25 заблокирован вашим провайдером")
        print("  - Фаервол блокирует исходящие соединения")
        print("  - MX сервер недоступен")
        return False
    except TimeoutError:
        print(f"\n✗ Ошибка: Таймаут соединения с {mx_server}:{SMTP_PORT}")
        return False
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Основная функция"""
    print("=" * 60)
    print("  ОТПРАВКА EMAIL С ИЗМЕНЕННОЙ ДАТОЙ")
    print("  Дипломная работа по кибербезопасности")
    print("=" * 60)
    
    # Извлекаем домен получателя
    recipient_domain = RECIPIENT_EMAIL.split('@')[1]
    print(f"\n📋 Конфигурация:")
    print(f"   Отправитель: {SENDER_EMAIL}")
    print(f"   Получатель: {RECIPIENT_EMAIL}")
    print(f"   Домен получателя: {recipient_domain}")
    print(f"   Поддельная дата: {FAKE_DATE}")
    
    # Получаем MX сервер
    print(f"\n🔍 Поиск MX сервера для {recipient_domain}...")
    mx_server = get_mx_server(recipient_domain)
    
    if not mx_server:
        print("\n✗ Не удалось получить MX сервер. Отмена.")
        sys.exit(1)
    
    print(f"✓ MX сервер найден: {mx_server}")
    
    # Преобразуем дату
    fake_date_rfc = parse_fake_date(FAKE_DATE)
    
    # Создаем письмо
    print(f"\n📝 Создание письма...")
    msg = create_email_with_attachments(
        SENDER_EMAIL,
        RECIPIENT_EMAIL,
        EMAIL_SUBJECT,
        EMAIL_BODY,
        fake_date_rfc,
        ATTACHMENTS
    )
    
    # Отправляем
    success = send_email_direct(mx_server, SENDER_EMAIL, RECIPIENT_EMAIL, msg)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ УСПЕШНО!")
        print("=" * 60)
        print("\n📬 Проверьте почтовый ящик:")
        print(f"   {RECIPIENT_EMAIL}")
        print("\n🔍 Для анализа заголовков:")
        print("   1. Откройте полученное письмо")
        print("   2. Найдите опцию 'Показать оригинал' или 'View source'")
        print("   3. Сравните заголовки Date и Received")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ ОШИБКА ОТПРАВКИ")
        print("=" * 60)
        print("\n💡 Возможные решения:")
        print("   1. Проверьте, что порт 25 не заблокирован")
        print("   2. Попробуйте использовать VPN")
        print("   3. Используйте вариант с Gmail relay (см. документацию)")
        sys.exit(1)


if __name__ == "__main__":
    main()
