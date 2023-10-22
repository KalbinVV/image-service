import asyncio
import os

from flask import Flask, render_template, request, send_file, abort
from sqlalchemy.orm import Session

import config
import db
from api import create_process_task
from db import init_tables
from utils import require_more_and_less_than

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Запрещаем входные файлы больше 5 мегабайт


@app.errorhandler(404)
def page_not_found(_e):
    return render_template('404.html'), 404


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_image', methods=['POST'])
async def upload_image():
    required_fields = {'width',
                       "height",
                       "quality",
                       "optimisation",
                       "result_format"}

    for required_field in required_fields:
        if required_field not in request.form.keys():
            return 'Invalid request', 400

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
        return 'Invalid request', 400

    if 'file' not in request.files.keys():
        return 'Invalid request', 400

    file = request.files.get('file')

    if file.content_type not in config.ALLOWED_FORMATS:
        return "Invalid file format", 400

    image_id = await create_process_task(file, width, height, quality, optimisation, result_format)

    return {'image_id': image_id}


@app.route("/get/<int:image_id>/", methods=["GET"])
async def get_image(image_id: int):
    with Session(bind=db.Engine) as session:
        image = session.query(db.Image).filter_by(id=image_id).first()

        if image is None or image.status == db.StatusEnum.cancelled:
            abort(404)

        if image.status == db.StatusEnum.completed:
            if os.path.exists(image.result_file_path):
                return send_file(image.result_file_path)

            abort(404)

        return render_template('please-wait.html')


async def main():
    init_tables()

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == '__main__':
    asyncio.run(main())
