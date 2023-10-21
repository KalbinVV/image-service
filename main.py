import asyncio
import logging
import os

from flask import Flask, render_template, request, send_file, url_for
from sqlalchemy.orm import Session

import config
import db
from api import create_process_task
from db import init_tables

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Запрещаем входные файлы больше 5 мегабайт


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload_image', methods=['POST'])
async def upload_image():
    required_fields = {'width', "height", "quality", "optimisation", "result_format"}

    for required_field in required_fields:
        if required_field not in request.form.keys():
            return 'Invalid request', 400

    try:
        width = int(request.form.get('width'))
        height = int(request.form.get('height'))
        quality = int(request.form.get('quality'))
        optimisation = bool(request.form.get('optimisation'))
        result_format = str(request.form.get("result_format"))
    except ValueError:
        return 'Invalid request', 400

    if width <= 0 or width > config.MAX_ALLOWED_WIDTH:
        return 'Invalid request', 400

    if height <= 0 or height > config.MAX_ALLOWED_HEIGHT:
        return 'Invalid request', 400

    if quality <= 0 or quality >= 100:
        return 'Invalid request', 400

    if 'file' not in request.files.keys():
        return 'Invalid request', 400

    file = request.files.get('file')

    if file.content_type not in config.ALLOWED_FORMATS:
        return "Invalid file format", 400

    image_id = await create_process_task(file, width, height, quality, optimisation, result_format)

    return {'image_id': image_id}


@app.route("/get", methods=["GET"])
async def get_image():
    if 'id' not in request.args.keys():
        return 'Invalid request', 400

    image_id = request.args.get('id')

    with Session(bind=db.Engine) as session:
        image = session.query(db.Image).filter_by(id=image_id).first()

        if image is None or image.status == db.StatusEnum.cancelled:
            return render_template("404.html"), 404

        if image.status == db.StatusEnum.completed:
            if os.path.exists(image.file_path):
                return send_file(image.file_path)

            return render_template("404.html"), 404

        return render_template('please-wait.html')


async def main():
    init_tables()

    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == '__main__':
    asyncio.run(main())

