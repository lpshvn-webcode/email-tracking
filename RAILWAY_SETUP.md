# 🚂 Railway Setup для гибридной архитектуры

## Проблема
При загрузке изображения генерируется ссылка `http://127.0.0.1:5000` вместо Railway URL.

## ✅ Решение

### 1️⃣ Установить переменную окружения на Railway

Зайдите в ваш проект на Railway:

1. Откройте ваш проект
2. Перейдите в **Settings** → **Variables**
3. Добавьте переменную:

```
BASE_URL = https://your-app-name.up.railway.app
```

**Замените** `your-app-name.up.railway.app` на ваш реальный Railway домен!

### 2️⃣ Найти ваш Railway URL

В Railway:
1. Откройте ваш проект
2. Перейдите в **Settings** → **Domains**
3. Скопируйте URL (например: `https://email-tracking-production-abc123.up.railway.app`)

### 3️⃣ Установить переменную

```
Переменная: BASE_URL
Значение: https://email-tracking-production-abc123.up.railway.app
```

(Используйте ваш реальный URL!)

### 4️⃣ Перезапустить деплой

После добавления переменной Railway автоматически перезапустится.

## 🎯 Результат

После этого:
- ✅ Загрузка изображения на Railway → URL будет `https://your-app.railway.app/view/...`
- ✅ Эти ссылки работают из интернета
- ✅ Tracking работает
- ✅ Изображение загружается автоматически

## 📋 Полный workflow:

### На Railway:
1. Открыть `https://your-app.railway.app/facebook`
2. Загрузить изображение
3. Получить ссылку: `https://your-app.railway.app/view/abc-123`

### Локально:
1. Открыть `http://127.0.0.1:8080/facebook`
2. Вставить Railway ссылку из шага 3
3. Заполнить форму
4. Отправить письмо

### У получателя:
1. Открывает письмо → видит Facebook дизайн
2. Кликает "Confirm Email"
3. Открывается Railway URL
4. **Изображение сразу загружается!**

## 🔍 Проверка BASE_URL

Код уже настроен правильно в `web_interface_advanced.py`:

```python
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')
image_url = f"{BASE_URL}/view/{tracking_id}"
```

Просто нужно установить переменную на Railway!

## ⚠️ Важно

- **Без `BASE_URL`** → ссылки будут `http://127.0.0.1:5000/view/...` (не работают из интернета)
- **С `BASE_URL`** → ссылки будут `https://your-app.railway.app/view/...` (работают везде!)

## 🚀 После настройки

Railway будет генерировать правильные ссылки:
- `https://your-app.railway.app/view/{id}` - для изображения
- `https://your-app.railway.app/tracking/{id}` - для статистики

А отправка писем идет с localhost через порт 25! 🎉
