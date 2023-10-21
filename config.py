import os
from dotenv import load_dotenv, find_dotenv
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv(find_dotenv())

DB_URL = os.environ.get('DB_URL')

HOST = os.environ.get('HOST')
PORT = int(os.environ.get('PORT'))
DEBUG = bool(os.environ.get('DEBUG'))

FILES_FOLDER = os.environ.get('FILES_FOLDER')

ALLOWED_FORMATS = {'image/png', 'image/jpeg'}

MAX_ALLOWED_WIDTH = 2000
MAX_ALLOWED_HEIGHT = 2000
