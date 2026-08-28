# English RPG

Мобильная PWA-игра для изучения английского языка вместе с кошкой Нагисой.

## Возможности MVP

- маршрут A2→B2 из 100 локаций и 5000 учебных точек, отдельно от 100 уровней игрока;
- задания нескольких типов, озвучка и проверочные упражнения;
- вход по приватному Player ID и имени;
- отдельный прогресс, XP и сердца для каждого игрока;
- адаптивный пиксельный интерфейс;
- установка на телефон как PWA;
- FastAPI backend и SQLite.

Долгосрочная структура курса описана в
[учебной программе A2→B2](docs/learning-roadmap.md). Полный машиночитаемый план
находится в `backend/app/curriculum.json`; первые две локации содержат 500 готовых заданий.

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

Проверка структуры и покрытия учебного контента:

```powershell
.\backend\venv\Scripts\python.exe scripts\validate_course.py `
    backend\app\curriculum.json backend\app\course_content.json `
    --report docs\course-coverage.md
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
