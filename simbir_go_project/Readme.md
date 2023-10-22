### Simbir.Go ###

1. **Установка зависимостей** 

Установить зависимости из файла `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

2. **Настройка базы данных** 

Внести настройки базы данных в файл `settings.py`. Заменить `your_db_name`, `your_db_user`, и `your_db_password` на ваши данные:
 
    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'your_db_name',
            'USER': 'your_db_user',
            'PASSWORD': 'your_db_password',
            'HOST': 'localhost',
            'PORT': '',  # По умолчанию - 5432
        }
    }
    ```

3. **Применение миграций**

Применить миграции для создания таблиц в базе данных:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

4. **Запуск сервера**

Запустить сервер:

    ```bash
    python manage.py runserver
    ```

## Документация API доступна по адресу `http://127.0.0.1:8000/swagger/` или `http://127.0.0.1:8000/redoc/` после запуска сервера.

**Создание учетной записи администратора**

Для создания первой учетной записи администартора необходимо выполнить комманду:

    ```bash
        python manage.py createsuperuser
    ```
После чего ввести Username и Password.

С помощью этого суперпользователя (админа) можно будет создавать другие admin аккаунты через сам API

