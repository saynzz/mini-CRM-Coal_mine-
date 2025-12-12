from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from database.db_connection import DatabaseConnection

class SectionManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_section_id = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление участками')
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_section)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_section)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_section)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Название', 'Площадь (га)', 'Высота (м)', 'Руководитель'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_section)
        
        layout.addWidget(self.table)
        
        # Статус
        self.status_label = QLabel('Готово')
        layout.addWidget(self.status_label)
    
    def load_data(self):
        try:
            query = """
            SELECT s.*, w.full_name as manager_name
            FROM sections s
            LEFT JOIN workers w ON s.manager_tab_number = w.tab_number
            ORDER BY s.section_name
            """
            results = self.db.fetch_all(query)
            
            self.table.setRowCount(len(results))
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['section_id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['section_name']))
                self.table.setItem(i, 2, QTableWidgetItem(f"{row['area']:.1f}" if row['area'] else ''))
                self.table.setItem(i, 3, QTableWidgetItem(f"{row['height']:.1f}" if row['height'] else ''))
                self.table.setItem(i, 4, QTableWidgetItem(row['manager_name'] if row['manager_name'] else 'Не назначен'))
            
            self.table.resizeColumnsToContents()
            self.status_label.setText(f'Загружено участков: {len(results)}')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_section(self):
        self.current_section_id = None
        self.show_section_dialog()
    
    def edit_section(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите участок для редактирования')
            return
        
        section_id = int(self.table.item(selected_row, 0).text())
        self.current_section_id = section_id
        self.show_section_dialog()
    
    def show_section_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование участка' if self.current_section_id else 'Добавление участка')
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        name_edit = QLineEdit()
        area_edit = QLineEdit()
        area_edit.setValidator(QDoubleValidator(0, 10000, 2))
        height_edit = QLineEdit()
        height_edit.setValidator(QDoubleValidator(0, 1000, 2))
        
        # Комбобокс для выбора руководителя
        manager_combo = QComboBox()
        manager_combo.addItem('Не назначен', None)
        
        try:
            query = "SELECT tab_number, full_name FROM workers ORDER BY full_name"
            workers = self.db.fetch_all(query)
            for worker in workers:
                manager_combo.addItem(worker['full_name'], worker['tab_number'])
        except Exception as e:
            print(f"Ошибка загрузки работников: {e}")
        
        # Загружаем данные для редактирования
        if self.current_section_id:
            query = "SELECT * FROM sections WHERE section_id = ?"
            section_data = self.db.fetch_one(query, (self.current_section_id,))
            
            if section_data:
                name_edit.setText(section_data['section_name'])
                area_edit.setText(str(section_data['area']) if section_data['area'] else '')
                height_edit.setText(str(section_data['height']) if section_data['height'] else '')
                
                # Устанавливаем руководителя
                for i in range(manager_combo.count()):
                    if manager_combo.itemData(i) == section_data['manager_tab_number']:
                        manager_combo.setCurrentIndex(i)
                        break
        
        layout.addRow('Название участка:', name_edit)
        layout.addRow('Площадь (га):', area_edit)
        layout.addRow('Высота (м):', height_edit)
        layout.addRow('Руководитель:', manager_combo)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_section(
            dialog, name_edit.text(), area_edit.text(), 
            height_edit.text(), manager_combo.currentData()
        ))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_section(self, dialog, name, area, height, manager_id):
        if not name.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите название участка')
            return
        
        try:
            area_value = float(area) if area else None
            height_value = float(height) if height else None
            
            if self.current_section_id:
                # Обновление существующего участка
                query = """
                UPDATE sections SET 
                    section_name = ?, 
                    area = ?, 
                    height = ?, 
                    manager_tab_number = ?
                WHERE section_id = ?
                """
                params = (name, area_value, height_value, manager_id, self.current_section_id)
            else:
                # Добавление нового участка
                query = """
                INSERT INTO sections (section_name, area, height, manager_tab_number)
                VALUES (?, ?, ?, ?)
                """
                params = (name, area_value, height_value, manager_id)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_section(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите участок для удаления')
            return
        
        section_id = int(self.table.item(selected_row, 0).text())
        section_name = self.table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить участок "{section_name}"?\n'
            'Внимание: это действие нельзя отменить.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM sections WHERE section_id = ?"
                self.db.execute_query(query, (section_id,))
                self.load_data()
                self.status_label.setText(f'Участок "{section_name}" удален')
            except Exception as e:
                if 'FOREIGN KEY constraint failed' in str(e):
                    QMessageBox.critical(
                        self, 'Ошибка удаления',
                        f'Невозможно удалить участок "{section_name}", '
                        'так как есть связанные данные (работники, добыча и др.).'
                    )
                else:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')