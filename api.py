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

    # Сохраняем путь до исходного файла в случае экстренного прерывания сервиса
    with Session(bind=db.Engine) as session:
        session.query(db.Image).filter_by(id=image_id).update({"source_file_path": file_path})

        session.commit()

    image = Image.open(file_path)

    image = image.resize((width, height), Image.LANCZOS)

    dst_path = os.path.join(config.FILES_FOLDER, f'image-{image_id}.{result_format}')

    # Сохраняем путь к результату, перед началом загрузки на диск, в случае перезагрузки
    with Session(bind=db.Engine) as session:
        session.query(db.Image).filter_by(id=image_id).update({
            "result_file_path": dst_path
        })

        session.commit()

    image.save(dst_path, format=result_format, optimize=optimisation, quality=quality)

    # Удаляем исходный файл после обработки
    os.remove(file_path)

    with Session(bind=db.Engine) as session:
        session.query(db.Image).filter_by(id=image_id).update({
            "status": db.StatusEnum.completed,
            "source_file_path": None
        })

        session.commit()

    logging.info(f"Задача завершена! (image_id: {image_id})")


# Удаляем задачи из базы данных, которые не были выполнены из-за прерывания работы сервиса
def process_cancelled_tasks():
    with Session(db.Engine) as session:
        tasks: list[type[db.Image]] = session.query(db.Image).filter_by(status=db.StatusEnum.processing).all()

        for task in tasks:
            result_file_path = task.result_file_path

            # Если файл начал загружаться, однако процесс был прерван
            if result_file_path is not None:
                if os.path.exists(result_file_path):
                    os.remove(result_file_path)

            source_file_path = task.source_file_path

            # Удаляем исходный файл, если система не успела его удалить
            if source_file_path and os.path.exists(source_file_path):
                os.remove(source_file_path)

            # Удаляем задачу, если не удалось восстановить её
            if task.status == db.StatusEnum.processing:
                session.delete(task)

        session.commit()
