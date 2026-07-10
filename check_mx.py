#!/usr/bin/env python3
"""
Утилита для проверки MX записей домена
Используется для определения SMTP сервера получателя
"""

import dns.resolver
import sys


def get_mx_records(domain):
    """
    Получить MX записи для домена
    
    Args:
        domain: Доменное имя (например, bientotmail.com)
    
    Returns:
        List of tuples: [(priority, mx_host), ...]
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        results = []
        
        print(f"\n✓ MX записи для домена '{domain}':")
        print("-" * 60)
        
        for mx in mx_records:
            priority = mx.preference
            host = str(mx.exchange).rstrip('.')
            results.append((priority, host))
            print(f"  Приоритет: {priority:3d} | Сервер: {host}")
        
        # Сортируем по приоритету (меньшее значение = выше приоритет)
        results.sort(key=lambda x: x[0])
        
        print("-" * 60)
        print(f"✓ Основной MX сервер: {results[0][1]}")
        
        return results
        
    except dns.resolver.NXDOMAIN:
        print(f"✗ Ошибка: Домен '{domain}' не существует")
        return []
    except dns.resolver.NoAnswer:
        print(f"✗ Ошибка: MX записи для домена '{domain}' не найдены")
        return []
    except Exception as e:
        print(f"✗ Ошибка при запросе MX записей: {e}")
        return []


def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    else:
        # По умолчанию проверяем домен получателя из config
        try:
            from config import RECIPIENT_EMAIL
            domain = RECIPIENT_EMAIL.split('@')[1]
            print(f"Используется домен из config: {domain}")
        except:
            print("Использование: python check_mx.py <domain>")
            print("Пример: python check_mx.py bientotmail.com")
            sys.exit(1)
    
    mx_records = get_mx_records(domain)
    
    if mx_records:
        print(f"\n💡 Для отправки используйте: {mx_records[0][1]}:{25}")
    else:
        print("\n✗ Не удалось получить MX записи")
        sys.exit(1)


if __name__ == "__main__":
    main()
