#!/usr/bin/env python3
"""
Продвинутый веб-интерфейс с хостингом изображений и tracking
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect
import smtplib
import dns.resolver
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from email.header import Header
from datetime import datetime
import os
import uuid
import json
from werkzeug.utils import secure_filename
from pathlib import Path
import quopri
from jinja2 import Template

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'hosted_images'
app.config['TRACKING_FOLDER'] = 'tracking_data'

# Создаем необходимые папки
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TRACKING_FOLDER'], exist_ok=True)
os.makedirs('uploads', exist_ok=True)


def save_tracking_info(tracking_id, info):
    """Сохранить информацию о просмотре"""
    tracking_file = os.path.join(app.config['TRACKING_FOLDER'], f'{tracking_id}.json')
    
    # Загружаем существующие данные если есть
    if os.path.exists(tracking_file):
        with open(tracking_file, 'r') as f:
            data = json.load(f)
    else:
        data = {
            'tracking_id': tracking_id,
            'created_at': datetime.now().isoformat(),
            'opens': []
        }
    
    # Добавляем новую информацию
    data['opens'].append(info)
    
    # Сохраняем
    with open(tracking_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
        dt_str = f"{date_str} {time_str}:00"
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        return formatdate(timeval=dt.timestamp(), localtime=True)
    except Exception as e:
        return formatdate(localtime=True)


def create_html_email_with_image(body, view_page_url, tracking_pixel_url):
    """Создать HTML письмо со ссылкой на страницу просмотра"""
    html = f"""
    <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                {body.replace(chr(10), '<br>')}
                
                <div style="margin: 30px 0; text-align: center;">
                    <a href="{view_page_url}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px;">
                        🖼️ Посмотреть фото
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 20px; text-align: center;">
                    Кликните на кнопку выше чтобы открыть изображение
                </p>
            </div>
            
            <!-- Tracking pixel -->
            <img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" alt="">
        </body>
    </html>
    """
    return html


def send_email_with_hosted_image(sender, recipient, subject, body, fake_date, 
                                 image_url, tracking_pixel_url, attachment_path=None):
    """Отправить email с размещенным изображением"""
    try:
        recipient_domain = recipient.split('@')[1]
        mx_server = get_mx_server(recipient_domain)
        
        if not mx_server:
            return False, f"Не удалось получить MX сервер для {recipient_domain}"
        
        # Создаем простое текстовое сообщение
        msg = MIMEText(f"{body}\n\n>>> LINK TO PHOTO: {image_url}\n\nClick link above to view!", 'plain', 'utf-8')
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Message-ID'] = make_msgid(domain=sender.split('@')[1])
        msg['Date'] = fake_date
        
        # Отправляем
        with smtplib.SMTP(mx_server, 25, timeout=30) as server:
            server.ehlo()
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
    """Главная страница"""
    return render_template('index_advanced.html')


@app.route('/facebook')
def facebook():
    """Facebook-style email sender"""
    return render_template('facebook_sender.html')


@app.route('/view/<image_id>')
def view_page(image_id):
    """Показать изображение напрямую и записать просмотр"""
    try:
        # Записываем информацию о просмотре
        tracking_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Direct'),
            'type': 'image_view'
        }
        save_tracking_info(image_id, tracking_info)
        
        # Ищем файл изображения
        image_dir = Path(app.config['UPLOAD_FOLDER'])
        image_files = list(image_dir.glob(f'{image_id}.*'))
        
        if image_files:
            # Отправляем файл для скачивания (не открывая в браузере)
            return send_file(
                image_files[0],
                as_attachment=True,
                download_name=image_files[0].name
            )
        else:
            return "Изображение не найдено", 404
            
    except Exception as e:
        return f"Ошибка: {str(e)}", 500


@app.route('/download/<image_id>')
def download_image(image_id):
    """Показать страницу авто-скачивания или текстовую страницу"""
    try:
        # Записываем информацию о просмотре страницы
        tracking_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Direct'),
            'type': 'download_page_view'
        }
        save_tracking_info(image_id, tracking_info)
        
        # Проверяем что файл существует
        image_dir = Path(app.config['UPLOAD_FOLDER'])
        image_files = list(image_dir.glob(f'{image_id}.*'))
        
        if not image_files:
            return "Изображение не найдено", 404
        
        # Читаем tracking данные чтобы узнать show_image
        tracking_file = os.path.join(app.config['TRACKING_FOLDER'], f'{image_id}.json')
        show_image = True  # По умолчанию показываем
        
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                data = json.load(f)
                show_image = data.get('show_image', True)
        
        BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
        download_url = f"{BASE_URL}/download_file/{image_id}"
        
        # Если show_image = True -> автоматически скачать (пустая страница)
        # Если show_image = False -> показать текст "Изображение было загружено"
        if show_image:
            return render_template('auto_download.html', download_url=download_url)
        else:
            return render_template('text_only.html')
            
    except Exception as e:
        return f"Ошибка: {str(e)}", 500


@app.route('/download_file/<image_id>')
def download_file(image_id):
    """Прямое скачивание файла (force download)"""
    try:
        # Записываем информацию о скачивании
        tracking_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Direct'),
            'type': 'file_download'
        }
        save_tracking_info(image_id, tracking_info)
        
        # Ищем файл изображения
        image_dir = Path(app.config['UPLOAD_FOLDER'])
        image_files = list(image_dir.glob(f'{image_id}.*'))
        
        if image_files:
            # FORCE DOWNLOAD - браузер должен скачать файл, а не открыть
            response = send_file(
                image_files[0],
                as_attachment=True,
                download_name=f"photo{image_files[0].suffix}"
            )
            # Дополнительные заголовки для принудительного скачивания
            response.headers['Content-Disposition'] = f'attachment; filename="photo{image_files[0].suffix}"'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        else:
            return "Изображение не найдено", 404
            
    except Exception as e:
        return f"Ошибка: {str(e)}", 500


@app.route('/download_page/<image_id>')
def download_page(image_id):
    """Показать страницу с кнопкой скачивания (старая версия)"""
    return render_template('view_image.html')


@app.route('/image/<image_id>')
def view_image(image_id):
    """Альтернативный маршрут для изображения"""
    try:
        # Записываем информацию о просмотре
        tracking_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Direct'),
            'type': 'image_view'
        }
        save_tracking_info(image_id, tracking_info)
        
        # Ищем файл изображения
        image_dir = Path(app.config['UPLOAD_FOLDER'])
        image_files = list(image_dir.glob(f'{image_id}.*'))
        
        if image_files:
            return send_file(image_files[0])
        else:
            return "Изображение не найдено", 404
            
    except Exception as e:
        return f"Ошибка: {str(e)}", 500


@app.route('/track_download/<tracking_id>', methods=['POST'])
def track_download(tracking_id):
    """Записать скачивание изображения"""
    try:
        tracking_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'referer': request.headers.get('Referer', 'Direct'),
            'type': 'download_click'
        }
        save_tracking_info(tracking_id, tracking_info)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/pixel/<tracking_id>.png')
def tracking_pixel(tracking_id):
    """1x1 прозрачный pixel для отслеживания открытия письма"""
    try:
        # Записываем открытие письма
        tracking_info = {
            'timestamp': datetime.now().isoformat(),
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown'),
            'type': 'email_open'
        }
        save_tracking_info(tracking_id, tracking_info)
        
        # Возвращаем 1x1 прозрачный PNG
        import io
        import base64
        
        # Минимальный прозрачный PNG (1x1 pixel)
        pixel_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        )
        
        return send_file(
            io.BytesIO(pixel_data),
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        # В случае ошибки все равно возвращаем pixel
        return '', 200


@app.route('/tracking/<tracking_id>')
def view_tracking(tracking_id):
    """Просмотр статистики tracking"""
    try:
        tracking_file = os.path.join(app.config['TRACKING_FOLDER'], f'{tracking_id}.json')
        
        if not os.path.exists(tracking_file):
            return jsonify({'error': 'Tracking ID не найден'}), 404
        
        with open(tracking_file, 'r') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Загрузить изображение и получить ссылку"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Изображение не загружено'
            })
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({
                'success': False,
                'message': 'Файл не выбран'
            })
        
        # Генерируем уникальный ID
        tracking_id = str(uuid.uuid4())
        
        # Получаем параметр show_image (1 = показывать, 0 = не показывать)
        show_image = request.form.get('show_image', '1') == '1'
        
        # Сохраняем файл
        ext = os.path.splitext(file.filename)[1]
        hosted_filename = f"{tracking_id}{ext}"
        hosted_path = os.path.join(app.config['UPLOAD_FOLDER'], hosted_filename)
        file.save(hosted_path)
        
        # Сохраняем конфигурацию show_image в tracking данные
        tracking_info = {
            'tracking_id': tracking_id,
            'created_at': datetime.now().isoformat(),
            'filename': file.filename,
            'show_image': show_image,
            'opens': []
        }
        tracking_file = os.path.join(app.config['TRACKING_FOLDER'], f'{tracking_id}.json')
        with open(tracking_file, 'w') as f:
            json.dump(tracking_info, f, indent=2, ensure_ascii=False)
        
        # Создаем URL (используем BASE_URL из переменных окружения или localhost)
        BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
        image_url = f"{BASE_URL}/download/{tracking_id}"
        tracking_url = f"{BASE_URL}/tracking/{tracking_id}"
        
        return jsonify({
            'success': True,
            'tracking_id': tracking_id,
            'image_url': image_url,
            'tracking_url': tracking_url,
            'message': 'Изображение загружено! Скопируйте ссылку и вставьте в письмо'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })


@app.route('/send', methods=['POST'])
def send():
    """Обработка отправки простого текстового письма"""
    try:
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        body = request.form.get('body')
        fake_date_str = request.form.get('fake_date')
        fake_time_str = request.form.get('fake_time')
        
        if not all([sender, recipient, subject, body, fake_date_str, fake_time_str]):
            return jsonify({
                'success': False,
                'message': 'Все поля обязательны для заполнения'
            })
        
        # Преобразуем дату
        fake_date = parse_datetime(fake_date_str, fake_time_str)
        
        # Получаем MX сервер
        recipient_domain = recipient.split('@')[1]
        mx_server = get_mx_server(recipient_domain)
        
        if not mx_server:
            return jsonify({
                'success': False,
                'message': f'Не удалось получить MX сервер для {recipient_domain}'
            })
        
        # Создаем простое текстовое сообщение
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Message-ID'] = make_msgid(domain=sender.split('@')[1])
        msg['Date'] = fake_date
        
        # Отправляем
        with smtplib.SMTP(mx_server, 25, timeout=30) as server:
            server.ehlo()
            try:
                server.starttls()
                server.ehlo()
            except:
                pass
            server.send_message(msg)
        
        return jsonify({
            'success': True,
            'message': f'Письмо успешно отправлено через {mx_server}',
            'fake_date': fake_date,
            'real_time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'tracking_url': 'N/A (используйте ссылку из Шага 1)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })


@app.route('/send_facebook', methods=['POST'])
def send_facebook():
    """Отправка письма в стиле Facebook с кнопкой Confirm"""
    try:
        recipient = request.form.get('recipient')
        user_name = request.form.get('user_name')
        confirm_url = request.form.get('confirm_url')  # Railway URL с изображением
        fake_date_str = request.form.get('fake_date')
        fake_time_str = request.form.get('fake_time')
        sender = request.form.get('sender', 'security@facebookmail.com')
        
        if not all([recipient, user_name, confirm_url, fake_date_str, fake_time_str]):
            return jsonify({
                'success': False,
                'message': 'Все поля обязательны для заполнения'
            })
        
        # Преобразуем дату
        fake_date = parse_datetime(fake_date_str, fake_time_str)
        
        # Читаем HTML шаблон
        with open('templates/facebook_style_email.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Рендерим шаблон
        template = Template(template_content)
        html_content = template.render(
            user_name=user_name,
            confirm_url=confirm_url,
            recipient_email=recipient
        )
        
        # Plain text версия
        text_content = f"""
Hi {user_name},

We got your request to add this email address to your account.

Confirm your email by visiting this link:
{confirm_url}

Don't share this confirmation with anyone.

Thanks,
Facebook Security

---
This message was sent to {recipient}
© Facebook. Meta Platforms, Inc.
"""
        
        # Создаем multipart сообщение
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{user_name}, confirm your email address'
        msg['From'] = f'Facebook <{sender}>'
        msg['To'] = recipient
        msg['Message-ID'] = make_msgid(domain=sender.split('@')[1])
        msg['Date'] = fake_date
        
        # Прикрепляем обе версии
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)
        
        # Получаем MX сервер
        recipient_domain = recipient.split('@')[1]
        mx_server = get_mx_server(recipient_domain)
        
        if not mx_server:
            return jsonify({
                'success': False,
                'message': f'Не удалось получить MX сервер для {recipient_domain}'
            })
        
        # Отправляем
        with smtplib.SMTP(mx_server, 25, timeout=30) as server:
            server.ehlo()
            try:
                server.starttls()
                server.ehlo()
            except:
                pass
            server.send_message(msg)
        
        return jsonify({
            'success': True,
            'message': f'Facebook-style письмо успешно отправлено через {mx_server}',
            'fake_date': fake_date,
            'real_time': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'confirm_url': confirm_url
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })


if __name__ == '__main__':
    import os
    
    # Получаем порт из переменной окружения (для Railway) или используем 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False') == 'True'
    
    print("=" * 60)
    print("  ПРОДВИНУТЫЙ WEB ИНТЕРФЕЙС С TRACKING")
    print("=" * 60)
    print(f"\n✓ Сервер запущен на: http://{host}:{port}")
    print("✓ Откройте браузер и перейдите по адресу выше")
    print("\n✨ Возможности:")
    print("  • Хостинг изображений на сервере")
    print("  • Отслеживание открытия писем")
    print("  • Отслеживание просмотра изображений")
    print("  • Сбор информации: IP, User-Agent, время")
    print("\n[Нажмите Ctrl+C для остановки]\n")
    
    app.run(debug=debug, host=host, port=port)
