# Описание

Разработать web-сервис для изменения размера и сжатия избражений. Предусмотреть офлоад обработки изображений в отдельные процессы от API. Веб-фреймворк использовать по выбору. Для работы с изображениями можно использовать pillow.
# Запуск:
## Через Docker:

git clone https://github.com/KalbinVV/image-service.git

cd image-service

docker build . --tag image-service:latest

docker run -i -t -p 5000:5000 --name image-service image-service:latest

## Без docker:

pip install -r requirements.txt

python main.py
