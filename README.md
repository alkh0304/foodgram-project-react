# Foodgram

## Описание:

Foodgram - сайт для опытных кулинаров и тех, кто просто решил попробовать что-то новое! Здесь вы сможете найти разнообразные рецепты, поделиться своими и даже подписаться на любимых авторов.

## Технологии и библиотеки:
- [Python](https://www.python.org/);
- [Django](https://www.djangoproject.com);
- [Django REST Framework](https://www.django-rest-framework.org);
- [PostgreSQL](https://www.postgresql.org);
- [Gunicorn](https://gunicorn.org);
- [NGINX](https://nginx.org/ru/);
- [Яндекс Облако](https://cloud.yandex.ru);
- [Docker](https://www.docker.com);
- [GIT](https://git-scm.com);
- [CI/CD github actions](https://github.com/features/actions).

## Статус проекта:

![example workflow](https://github.com/alkh0304/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## Как запустить проект:

- Клонировать репозиторий и перейти в него в командной строке

- Создайте .env файл в папке infra/ и заполните следующие переменные:

```
DB_ENGINE=django.db.backends.postgresql
```

```
DB_NAME= # имя БД
```

```
POSTGRES_USER= # логин для подключения к БД
```

```
POSTGRES_PASSWORD= # пароль для подключения к БД
```

```
DB_HOST=db
```

```
DB_PORT=5432
```

- Используя docker-compose, соберите образ в папке infra:

```
cd infra
```

```
docker-compose up -d --build
```

- Произведите миграции:

```
docker-compose exec web python manage.py migrate
```

- Создайте суперюзера для доступа к функциям администратора:

```
docker-compose exec web python manage.py createsuperuser
```

- Соберите статику:

```
docker-compose exec web python manage.py collectstatic --no-input
```

- Загрузите список ингредиентов на сайт, скопировав файл ingredients.csv из папки data в папку infra:

```
docker cp ingredients.csv <CONTAINER ID>:/code
```

```
docker exec -it <CONTAINER ID> bash
```

```
python foodgram/manage.py import_ingredients /app/ingredients.csv
```

## Над проектом [foodgram](https://github.com/alkh0304/foodgram-project-react) работал:

[Александр Хоменко](https://github.com/alkh0304)