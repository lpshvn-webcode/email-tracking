#!/usr/bin/env python3
"""
Веб-интерфейс для отправки email с измененной датой
Flask приложение с HTML формой
"""

from flask import Flask, render_template, request, jsonify
import smtplib
import dns.resolver
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Макс 16MB
app.config['UPLOAD_FOLDER'] = 'uploads'

# Создаем папку для загрузок если её нет
os.makedirs('uploads', exist_ok=True)


def get_mx_server(domain):
    """Получить MX сервер для домена"""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_list = [(mx.preference, str(mx.exchange).rstrip('.')) for mx in mx_records]
        mx_list.sort()
        return mx_list[0][1]
    except Exception as e:
        return None


def parse_datetime(date_str, time_str):
    """Преобразовать дату и время в RFC 2822 формат"""
    try:
        # date_str формат: YYYY-MM-DD
        # time_str формат: HH:MM
        dt_str = f"{date_str} {time_str}:00"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return formatdate(timeval=dt.timestamp(), localtime=True)
    except Exception as e:
        return formatdate(localtime=True)


def send_email(sender, recipient, subject, body, fake_date, attachment_path=None):
    """Отправить email с измененной датой"""
    try:
        # Получаем домен получателя
        recipient_domain = recipient.split('@')[1]
        
        # Получаем MX сервер
        mx_server = get_mx_server(recipient_domain)
        if not mx_server:
            return False, f"Не удалось получить MX сервер для {recipient_domain}"
        
        # Создаем сообщение
        msg = EmailMessage()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = subject
        msg['Message-ID'] = make_msgid(domain=sender.split('@')[1])
        msg['Date'] = fake_date
        
        # Устанавливаем тело письма с правильной кодировкой
        msg.set_content(body, charset='utf-8')
        
        # Прикрепляем файл если есть
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(attachment_path)
                
                # Определяем MIME тип файла
                import mimetypes
                mime_type, _ = mimetypes.guess_type(attachment_path)
                
                if mime_type is None:
                    # Если не удалось определить, используем по умолчанию
                    maintype = 'application'
                    subtype = 'octet-stream'
                else:
                    maintype, subtype = mime_type.split('/', 1)
                
                msg.add_attachment(file_data, 
                                 maintype=maintype, 
                                 subtype=subtype, 
                                 filename=file_name)
        
        # Отправляем
        with smtplib.SMTP(mx_server, 25, timeout=30) as server:
            server.ehlo()
            
            # Пытаемся использовать STARTTLS
            try:
                server.starttls()
                server.ehlo()
            except:
                pass
            
            server.send_message(msg)
        
        return True, f"Письмо успешно отправлено через {mx_server}"
        
    except Exception as e:
        return False, f"Ошибка отправки: {str(e)}"


@app.route('/')
def index():
    """Главная страница с формой"""
    return render_template('index.html')


@app.route('/send', methods=['POST'])
def send():
    """Обработка отправки формы"""
    try:
        # Получаем данные из формы
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        body = request.form.get('body')
        fake_date_str = request.form.get('fake_date')
        fake_time_str = request.form.get('fake_time')
        
        # Проверяем обязательные поля
        if not all([sender, recipient, subject, body, fake_date_str, fake_time_str]):
            return jsonify({
                'success': False,
                'message': 'Все поля обязательны для заполнения'
            })
        
        # Обрабатываем вложение
        attachment_path = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = secure_filename(file.filename)
                attachment_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(attachment_path)
        
        # Преобразуем дату
        fake_date = parse_datetime(fake_date_str, fake_time_str)
        
        # Отправляем
        success, message = send_email(sender, recipient, subject, body, fake_date, attachment_path)
        
        # Удаляем временный файл
        if attachment_path and os.path.exists(attachment_path):
            try:
                os.remove(attachment_path)
            except:
                pass
        
        return jsonify({
            'success': success,
            'message': message,
            'fake_date': fake_date,
            'real_time': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })


if __name__ == '__main__':
    print("=" * 60)
    print("  WEB ИНТЕРФЕЙС ДЛЯ ОТПРАВКИ EMAIL С ИЗМЕНЕННОЙ ДАТОЙ")
    print("=" * 60)
    print("\n✓ Сервер запущен на: http://127.0.0.1:5000")
    print("✓ Откройте браузер и перейдите по адресу выше")
    print("\n[Нажмите Ctrl+C для остановки]\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
