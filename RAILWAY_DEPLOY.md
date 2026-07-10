# 🚂 Деплой на Railway

## 📋 Что нужно:

1. Аккаунт на [Railway.app](https://railway.app)
2. GitHub аккаунт
3. Этот проект

## 🚀 Пошаговая инструкция:

### Шаг 1: Подготовка проекта

Проект уже готов! Есть все необходимые файлы:
- ✅ `Procfile` - команда запуска для Railway
- ✅ `requirements.txt` - зависимости Python
- ✅ `web_interface_advanced.py` - настроен для production

### Шаг 2: Создание Git репозитория

```bash
cd /Users/rabota/Desktop/email_backdating

# Инициализируем git
git init

# Создаем .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.DS_Store
hosted_images/
tracking_data/
uploads/
*.log
EOF

# Добавляем файлы
git add .
git commit -m "Initial commit: Email backdating with tracking"
```

### Шаг 3: Создание GitHub репозитория

1. Зайдите на [GitHub.com](https://github.com)
2. Нажмите "New repository"
3. Название: `email-tracking` (или любое другое)
4. Сделайте репозиторий **Private** ⚠️
5. НЕ добавляйте README, .gitignore, license
6. Создайте репозиторий

### Шаг 4: Push в GitHub

```bash
# Добавьте удаленный репозиторий (замените YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/email-tracking.git

# Push
git branch -M main
git push -u origin main
```

### Шаг 5: Деплой на Railway

1. Зайдите на [Railway.app](https://railway.app)
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Выберите ваш репозиторий `email-tracking`
5. Railway автоматически:
   - Определит что это Python проект
   - Установит зависимости из `requirements.txt`
   - Запустит команду из `Procfile`

### Шаг 6: Получение URL

После деплоя:
1. Откройте "Settings" проекта
2. Найдите "Domains"
3. Нажмите "Generate Domain"
4. Вы получите URL типа: `https://your-app.up.railway.app`

### Шаг 7: Обновление URL в коде

Теперь нужно обновить хардкоженные URL в коде.

**Вариант A: Использовать переменную окружения (рекомендуется)**

В Railway Settings → Variables добавьте:
```
BASE_URL=https://your-app.up.railway.app
```

Обновите код в `web_interface_advanced.py`:

```python
# В функции upload_image(), строка ~290
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
image_url = f"{BASE_URL}/view/{tracking_id}"
tracking_url = f"{BASE_URL}/tracking/{tracking_id}"
```

**Вариант B: Хардкод (быстрее, но не гибко)**

Просто замените в коде:
```python
# Было:
image_url = f"http://127.0.0.1:5000/view/{tracking_id}"

# Стало:
image_url = f"https://your-app.up.railway.app/view/{tracking_id}"
```

### Шаг 8: Коммит и Push

```bash
git add .
git commit -m "Update URLs for Railway"
git push
```

Railway автоматически перезадеплоит проект!

## 🎯 Использование:

### Генерация ссылки:
1. Откройте `https://your-app.up.railway.app`
2. Загрузите фото
3. Нажмите "Сгенерировать ссылку"
4. Скопируйте ссылку

### Отправка письма:
1. Вставьте ссылку в текст письма
2. Отправьте письмо
3. Получатель откроет ссылку с любого устройства!

### Просмотр статистики:
```
https://your-app.up.railway.app/tracking/YOUR-ID
```

## ⚠️ Важно:

### Хранение файлов

Railway использует **эфемерное хранилище** - файлы удаляются при перезапуске!

**Решение 1: Использовать Cloudinary (бесплатно)**
- Регистрация на cloudinary.com
- API для загрузки изображений
- Постоянное хранилище

**Решение 2: AWS S3**
- Платное, но надежное
- Много места

**Решение 3: Railway Volume (платно)**
- Постоянное хранилище на Railway

### Tracking данных

Для постоянного хранения tracking используйте БД:
- **Railway PostgreSQL** (встроенная)
- **MongoDB Atlas** (бесплатно до 512MB)
- **SQLite** + Railway Volume

## 📊 Мониторинг:

В Railway Dashboard вы увидите:
- 📈 Логи в реальном времени
- 💾 Использование памяти
- 🔄 Статус деплоя
- 🌐 HTTP трафик

## 💰 Цены Railway:

- **Free Tier**: $5 кредитов/месяц (хватит на тесты)
- **Hobby**: $5/месяц
- **Pro**: $20/месяц

Для дипломной работы Free Tier должно хватить!

## 🔧 Troubleshooting:

### Ошибка: Module not found
```bash
# Обновите requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update requirements"
git push
```

### Ошибка: Port already in use
- Railway автоматически задает PORT
- Код уже настроен: `port = int(os.environ.get('PORT', 5000))`

### Приложение не открывается
- Проверьте логи в Railway Dashboard
- Убедитесь что Procfile правильный
- Host должен быть `0.0.0.0` (уже настроено)

## ✅ Checklist перед деплоем:

- [ ] Procfile создан
- [ ] requirements.txt обновлен
- [ ] .gitignore создан
- [ ] Git репозиторий инициализирован
- [ ] Код залит на GitHub
- [ ] Railway проект создан
- [ ] Domain сгенерирован
- [ ] BASE_URL обновлен
- [ ] Тестовая отправка работает

---

**Готово! Теперь ваше приложение доступно из интернета!** 🎉

