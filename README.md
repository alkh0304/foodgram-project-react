# Foodgram

[Ссылка на запущенный проект](http://84.201.143.178)

Доступ к администрированию сайта:

```
логин: admin@gmail.com
пароль: admin
```

## Описание:

Foodgram - сайт для опытных кулинаров и тех, кто просто решил попробовать что-то новое! Здесь вы сможете найти разнообразные рецепты, поделиться своими и даже подписаться на любимых авторов.

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