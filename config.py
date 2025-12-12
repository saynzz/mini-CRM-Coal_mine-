import os
from pathlib import Path

class Config:
    # настры SQLite базы данных
    DB_NAME = 'mine.db'
    DB_PATH = Path(__file__).parent / DB_NAME
    # настры путей
    BASE_DIR = Path(__file__).parent
    REPORTS_DIR = BASE_DIR / 'reports'
    HELP_FILE = BASE_DIR / 'help' / 'help.html'
    # создание директории при необходимости
    REPORTS_DIR.mkdir(exist_ok=True)
    APP_NAME = "Управление угольной шахтой"
    APP_VERSION = "1.0"