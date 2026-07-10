"""
SMTP Configuration для отправки писем

Для работы на Railway нужен внешний SMTP сервис.
"""

import os

# SMTP Configuration
SMTP_SETTINGS = {
    # Gmail SMTP (рекомендуется)
    'gmail': {
        'host': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True,
        'username': os.environ.get('SMTP_USERNAME', ''),  # your.email@gmail.com
        'password': os.environ.get('SMTP_PASSWORD', ''),  # app password
    },
    
    # SendGrid
    'sendgrid': {
        'host': 'smtp.sendgrid.net',
        'port': 587,
        'use_tls': True,
        'username': 'apikey',
        'password': os.environ.get('SENDGRID_API_KEY', ''),
    },
    
    # Mailgun
    'mailgun': {
        'host': 'smtp.mailgun.org',
        'port': 587,
        'use_tls': True,
        'username': os.environ.get('MAILGUN_USERNAME', ''),
        'password': os.environ.get('MAILGUN_PASSWORD', ''),
    },
    
    # Direct SMTP (работает только локально)
    'direct': {
        'host': None,  # Определяется через MX записи
        'port': 25,
        'use_tls': False,
        'username': None,
        'password': None,
    }
}

# Выбор SMTP провайдера
SMTP_PROVIDER = os.environ.get('SMTP_PROVIDER', 'direct')

def get_smtp_config():
    """Получить настройки SMTP"""
    return SMTP_SETTINGS.get(SMTP_PROVIDER, SMTP_SETTINGS['direct'])
