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

image_processing_tasks = set()


async def create_process_task(file: FileStorage, width: int, height: int,
                              quality: int, optimisation: bool, result_format: str) -> int:
    with Session(bind=db.Engine) as session:
        image = db.Image(loaded_at=datetime.datetime.now(), status=db.StatusEnum.processing)

        session.add(image)
        session.commit()

        task = asyncio.create_task(process_image(file, width, height, quality,
                                                 optimisation, result_format, image.id))

        image_processing_tasks.add(task)

        logging.info(f"Новая задача... (image_id: {image.id})")

        task.add_done_callback(image_processing_tasks.discard)

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
            "file_path": dst_path,
            "status": db.StatusEnum.completed
        })

        session.commit()

    os.remove(file_path)

    logging.info(f"Задача завершена! (image_id: {image_id})")
