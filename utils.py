import os.path
import typing
from typing import Any

from werkzeug.datastructures import FileStorage

import config


def save_file(file: FileStorage, file_id: int) -> str:
    dst_path = os.path.join(config.FILES_FOLDER, f'source-image-{file_id}')

    if not os.path.exists(config.FILES_FOLDER):
        os.makedirs(config.FILES_FOLDER)

    file.save(dst_path)

    return dst_path


def require_more_and_less_than(value: int, min_value: int, max_value: int) -> int | typing.NoReturn:
    if value < min_value or value > max_value:
        raise ValueError

    return value
