import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui.main_window import MainWindow
from database.db_connection import DatabaseConnection

def init_database():
    db = DatabaseConnection()
    
    if not db.table_exists('positions'):
        QMessageBox.information(
            None, 'Инициализация базы данных',
            'База данных не найдена. Создаю структуру и тестовые данные...'
        )
        from create_database import create_tables
        create_tables()
        return True
    return False

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    init_database()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()