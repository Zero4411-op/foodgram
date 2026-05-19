# Foodgram

Сервис для публикации рецептов. Пользователи могут создавать рецепты, подписываться на авторов, добавлять рецепты в избранное и формировать список покупок.

## Стек технологий

- Python 3.12, Django 5.1, Django REST Framework
- PostgreSQL 13
- Docker, Docker Compose
- Nginx, Gunicorn
- React, Node.js 18
- GitHub Actions (CI/CD)

## Локальный запуск

1. Клонировать репозиторий:
```bash
git clone https://github.com/Zero4411-op/foodgram.git
cd foodgram

2.Создать .env файл в папке infra/:

POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_DB=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

2.Запустить контейнеры:

cd infra
docker compose up -d

4.Выполнить миграции и собрать статику:

docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic --noinput
docker compose exec backend python manage.py load_ingredients

5.Создать суперпользователя:

docker compose exec backend python manage.py createsuperuser
Проект доступен по адресу: http://localhost

```

## Примеры запросов к API
```bash
GET /api/recipes/ — список рецептов

POST /api/recipes/ — создать рецепт

GET /api/recipes/{id}/ — детали рецепта

POST /api/recipes/{id}/favorite/ — добавить в избранное

POST /api/recipes/{id}/shopping_cart/ — добавить в список покупок

GET /api/recipes/download_shopping_cart/ — скачать список покупок

GET /api/users/subscriptions/ — мои подписки

POST /api/users/{id}/subscribe/ — подписаться на автора

```

## Полная спецификация API доступна по адресу: /api/docs/

Развёрнутый проект
Проект доступен по адресу: http://158.160.225.140:7000

### Автор
Zero4411-op