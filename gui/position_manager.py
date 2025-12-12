from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from database.db_connection import DatabaseConnection

class PositionManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_position_id = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление должностями')
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_position)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_position)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_position)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(['ID', 'Наименование должности'])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_position)
        
        layout.addWidget(self.table)
        
        # Статус
        self.status_label = QLabel('Готово')
        layout.addWidget(self.status_label)
    
    def load_data(self):
        try:
            query = "SELECT * FROM positions ORDER BY position_name"
            results = self.db.fetch_all(query)
            
            self.table.setRowCount(len(results))
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['position_id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['position_name']))
            
            self.table.resizeColumnsToContents()
            self.status_label.setText(f'Загружено должностей: {len(results)}')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_position(self):
        self.current_position_id = None
        self.show_position_dialog()
    
    def edit_position(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите должность для редактирования')
            return
        
        position_id = int(self.table.item(selected_row, 0).text())
        self.current_position_id = position_id
        self.show_position_dialog()
    
    def show_position_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование должности' if self.current_position_id else 'Добавление должности')
        
        layout = QFormLayout(dialog)
        
        # Поле ввода
        name_edit = QLineEdit()
        
        # Загружаем данные для редактирования
        if self.current_position_id:
            query = "SELECT * FROM positions WHERE position_id = ?"
            position_data = self.db.fetch_one(query, (self.current_position_id,))
            
            if position_data:
                name_edit.setText(position_data['position_name'])
        
        layout.addRow('Наименование должности:', name_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_position(dialog, name_edit.text()))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_position(self, dialog, name):
        if not name.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите наименование должности')
            return
        
        try:
            if self.current_position_id:
                # Обновление существующей должности
                query = "UPDATE positions SET position_name = ? WHERE position_id = ?"
                params = (name, self.current_position_id)
            else:
                # Добавление новой должности
                query = "INSERT INTO positions (position_name) VALUES (?)"
                params = (name,)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_position(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите должность для удаления')
            return
        
        position_id = int(self.table.item(selected_row, 0).text())
        position_name = self.table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить должность "{position_name}"?\n'
            'Внимание: если есть работники с этой должностью, удаление будет невозможно.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM positions WHERE position_id = ?"
                self.db.execute_query(query, (position_id,))
                self.load_data()
                self.status_label.setText(f'Должность "{position_name}" удалена')
            except Exception as e:
                if 'FOREIGN KEY constraint failed' in str(e):
                    QMessageBox.critical(
                        self, 'Ошибка удаления',
                        f'Невозможно удалить должность "{position_name}", '
                        'так как есть работники с этой должностью.'
                    )
                else:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')