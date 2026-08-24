# English RPG

Мобильная PWA-игра для изучения английского языка вместе с кошкой Нагисой.

## Возможности MVP

- карта из 100 уровней и система опыта;
- задания нескольких типов, озвучка и проверочные упражнения;
- вход по приватному Player ID и имени;
- отдельный прогресс, XP и сердца для каждого игрока;
- адаптивный пиксельный интерфейс;
- установка на телефон как PWA;
- FastAPI backend и SQLite.

> В MVP Player ID выполняет роль ключа доступа. Не используйте короткий или
> легко угадываемый ID и не публикуйте его.

## Локальный запуск

Требуется Python 3.11 или новее.

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

После запуска приложение доступно по адресу `http://127.0.0.1:8000`.

## Тесты

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend:

```powershell
Get-ChildItem frontend/tests -Filter *.test.js | ForEach-Object {
    node $_.FullName
}
```

## Деплой в Amvera

Проект настроен файлом `amvera.yaml`:

- Python 3.11;
- один Uvicorn worker для тарифа со 100 МБ RAM;
- внутренний порт `5000`;
- постоянное хранилище подключено к `/data`;
- SQLite автоматически создаётся по пути `/data/game.db`.

После успешного развёртывания проверьте:

- `/` — интерфейс игры;
- `/api/health` — состояние приложения и SQLite.

Локальные файлы SQLite не загружаются в Git. При первом запуске в Amvera
создаётся новая база. Если требуется перенести локальный прогресс, файл
`game.db` нужно отдельно загрузить в папку **Data** через панель Amvera.

## Обновления

Изменения отправляются в ветку `main`. GitHub Actions запускает backend- и
frontend-тесты. После подключения webhook Amvera успешный push в `main`
автоматически запускает новую сборку; данные в `/data` при этом сохраняются.
