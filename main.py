import os

from flask import Flask, render_template, request, send_file, abort
from sqlalchemy.orm import Session

import config
import db
from api import create_process_task, process_cancelled_tasks
from db import init_tables
from utils import require_more_and_less_than

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Запрещаем входные файлы больше 5 мегабайт


@app.errorhandler(404)
def page_not_found(_e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html', allowed_formats=', '.join(config.ALLOWED_FORMATS))


@app.route('/upload_image', methods=['POST'])
async def upload_image():
    required_fields = {'width',
                       "height",
                       "quality",
                       "optimisation",
                       "result_format"}

    # Проверяем были ли отправлены все необходимые поля
    for required_field in required_fields:
        if required_field not in request.form.keys():
            return 'Неправильные входные данные', 400

    #  Проверяем правильного ли они типа и значения
    try:
        width = require_more_and_less_than(int(request.form.get('width')),
                                           config.MIN_ALLOWED_WIDTH,
                                           config.MAX_ALLOWED_WIDTH)
        height = require_more_and_less_than(int(request.form.get('height')),
                                            config.MIN_ALLOWED_HEIGHT,
                                            config.MAX_ALLOWED_HEIGHT)

        quality = require_more_and_less_than(int(request.form.get('quality')),
                                             min_value=1,
                                             max_value=100)

        optimisation = bool(request.form.get('optimisation'))
        result_format = request.form.get("result_format")

        if result_format not in config.ALLOWED_RESULT_FORMATS:
            raise ValueError()

    except ValueError:
        return 'Неправильные входные данные', 400

    #  Если пользователь не отправил файл
    if 'file' not in request.files.keys():
        return 'Неправильные входные данные', 400

    file = request.files.get('file')

    if file.content_type not in config.ALLOWED_FORMATS:
        return "Неправильный формат файла", 400

    image_id = await create_process_task(file, width, height, quality, optimisation, result_format)

    return {'image_id': image_id}


@app.route("/get/<int:image_id>/", methods=["GET"])
async def get_image(image_id: int):
    with Session(bind=db.Engine) as session:
        image = session.query(db.Image).filter_by(id=image_id).first()

        if image is None:
            abort(404)

        if image.status == db.StatusEnum.completed:
            # Если файл существует в базе данных, но его удалили из хранилища
            if os.path.exists(image.result_file_path):
                return send_file(image.result_file_path)

            abort(404)

        return render_template('please-wait.html')


def main():
    init_tables()

    # Обрабатываем задачи, которые не удалось завершить после перезагрузки
    process_cancelled_tasks()

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == '__main__':
    main()
