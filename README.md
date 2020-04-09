# recipe-service

recipe-service backend

Стек технологий: FastApi, PostgreSQL
Для взаимодействия с БД была использована библиотека SqlAlchemy

Сервис разворачивается на Docker Containers (Recipe-Service and PostgreSQL), Dockerfile и docker-compose.yaml в проекте
присутвтуют

Все необходимые зависимости для работы сервиса расположены в requirements.txt

Написаны unittests для проверки работоспостобности сервиса, покрыты основные функции сервиса

В директориях:
- database расположены ORM и Pydantic модели, а также подключение к БД
- routes расположены все маршруты API
- service расположены модули с функционалом API
- tests расположены unittests
- utils расположены дополнитьльные модули с дополнительным функционалом