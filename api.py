import asyncio
import datetime
import logging
import os.path

from sqlalchemy.orm import Session
from werkzeug.datastructures import FileStorage

import config
import db
from utils import save_file

from PIL import Image

# Все текущие задачи по обработке изображений
processing_tasks: set[asyncio.Task] = set()


async def create_process_task(file: FileStorage, width: int, height: int,
                              quality: int, optimisation: bool, result_format: str) -> int:
    with Session(bind=db.Engine) as session:
        image = db.Image(loaded_at=datetime.datetime.now(),
                         status=db.StatusEnum.processing)

        session.add(image)
        session.commit()

        task = asyncio.create_task(process_image(file, width, height, quality,
                                                 optimisation, result_format, image.id))

        processing_tasks.add(task)

        task.add_done_callback(processing_tasks.discard)

        logging.info(f"Новая задача... (image_id: {image.id})")

        return image.id


async def process_image(file: FileStorage, width: int, height: int, quality: int,
                        optimisation: bool, result_format: str, image_id: int) -> None:
    logging.info(f"Обработка задачи... (image_id: {image_id})")

    file_path = save_file(file, image_id)

    image = Image.open(file_path)

    image = image.resize((width, height), Image.LANCZOS)

    dst_path = os.path.join(config.FILES_FOLDER, f'image-{image_id}.{result_format}')

    image.save(dst_path, format=result_format, optimize=optimisation, quality=quality)

    with Session(bind=db.Engine) as session:
        session.query(db.Image).filter_by(id=image_id).update({
            "result_file_path": dst_path,
            "status": db.StatusEnum.completed
        })

        session.commit()

    # Удаляем исходный файл после обработки
    os.remove(file_path)

    logging.info(f"Задача завершена! (image_id: {image_id})")


def cancel_all_current_tasks():
    # Завершаем все текущие задачи
    for task in processing_tasks:
        task.cancel()

    with Session(bind=db.Engine) as session:
        # Обозначаем все незаконченные задачи в базе данных как прерванные
        session.query(db.Image).filter_by(status=db.StatusEnum.processing).update({
            "status": db.StatusEnum.cancelled
        })

        session.commit()
