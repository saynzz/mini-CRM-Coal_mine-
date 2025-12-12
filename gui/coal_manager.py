from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator 
from database.db_connection import DatabaseConnection

class CoalManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_coal = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление марками угля')
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        self.add_btn = QPushButton('Добавить')
        self.add_btn.clicked.connect(self.add_coal)
        
        self.edit_btn = QPushButton('Редактировать')
        self.edit_btn.clicked.connect(self.edit_coal)
        
        self.delete_btn = QPushButton('Удалить')
        self.delete_btn.clicked.connect(self.delete_coal)
        
        self.refresh_btn = QPushButton('Обновить')
        self.refresh_btn.clicked.connect(self.load_data)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Таблица с данными
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            'Марка угля', 'Зольность, %', 'Влажность, %', 
            'Теплота сгорания, ккал/кг', 'Стоимость 1 тн, руб.'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_coal)
        
        layout.addWidget(self.table)
        
        # Статус
        self.status_label = QLabel('Готово')
        layout.addWidget(self.status_label)
    
    def load_data(self):
        try:
            query = "SELECT * FROM coal ORDER BY coal_mark"
            results = self.db.fetch_all(query)
            
            self.table.setRowCount(len(results))
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(row['coal_mark']))
                self.table.setItem(i, 1, QTableWidgetItem(f"{row['ash_content']:.1f}" if row['ash_content'] else ''))
                self.table.setItem(i, 2, QTableWidgetItem(f"{row['moisture']:.1f}" if row['moisture'] else ''))
                self.table.setItem(i, 3, QTableWidgetItem(str(row['calorific_value']) if row['calorific_value'] else ''))
                self.table.setItem(i, 4, QTableWidgetItem(f"{row['price_per_ton']:,.0f}" if row['price_per_ton'] else ''))
            
            self.table.resizeColumnsToContents()
            self.status_label.setText(f'Загружено записей: {len(results)}')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_coal(self):
        self.current_coal = None
        self.show_coal_dialog()
    
    def edit_coal(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите марку угля для редактирования')
            return
        
        coal_mark = self.table.item(selected_row, 0).text()
        self.current_coal = coal_mark
        self.show_coal_dialog()
    
    def show_coal_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование марки угля' if self.current_coal else 'Добавление марки угля')
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        coal_edit = QLineEdit()
        ash_edit = QLineEdit()
        moisture_edit = QLineEdit()
        calorific_edit = QLineEdit()
        price_edit = QLineEdit()
        
        # Валидаторы
        ash_edit.setValidator(QDoubleValidator(0, 100, 2))
        moisture_edit.setValidator(QDoubleValidator(0, 100, 2))
        calorific_edit.setValidator(QIntValidator(0, 10000))
        price_edit.setValidator(QDoubleValidator(0, 1000000, 2))
        
        # Загружаем данные для редактирования
        if self.current_coal:
            query = "SELECT * FROM coal WHERE coal_mark = ?"
            coal_data = self.db.fetch_one(query, (self.current_coal,))
            
            if coal_data:
                coal_edit.setText(coal_data['coal_mark'])
                coal_edit.setReadOnly(True)  # Нельзя менять марку
                ash_edit.setText(str(coal_data['ash_content']) if coal_data['ash_content'] else '')
                moisture_edit.setText(str(coal_data['moisture']) if coal_data['moisture'] else '')
                calorific_edit.setText(str(coal_data['calorific_value']) if coal_data['calorific_value'] else '')
                price_edit.setText(str(coal_data['price_per_ton']) if coal_data['price_per_ton'] else '')
        
        layout.addRow('Марка угля:', coal_edit)
        layout.addRow('Зольность, %:', ash_edit)
        layout.addRow('Влажность, %:', moisture_edit)
        layout.addRow('Теплота сгорания, ккал/кг:', calorific_edit)
        layout.addRow('Стоимость 1 тн, руб.:', price_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_coal(
            dialog, coal_edit.text(), ash_edit.text(), 
            moisture_edit.text(), calorific_edit.text(), price_edit.text()
        ))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        
        dialog.exec_()
    
    def save_coal(self, dialog, coal_mark, ash, moisture, calorific, price):
        # Валидация
        if not coal_mark.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите марку угля')
            return
        
        try:
            ash_value = float(ash) if ash else None
            moisture_value = float(moisture) if moisture else None
            calorific_value = int(calorific) if calorific else None
            price_value = float(price) if price else None
            
            if self.current_coal:
                # Обновление существующей записи
                query = """
                UPDATE coal SET 
                    ash_content = ?, 
                    moisture = ?, 
                    calorific_value = ?, 
                    price_per_ton = ?
                WHERE coal_mark = ?
                """
                params = (ash_value, moisture_value, calorific_value, price_value, coal_mark)
            else:
                # Добавление новой записи
                query = """
                INSERT INTO coal (coal_mark, ash_content, moisture, calorific_value, price_per_ton)
                VALUES (?, ?, ?, ?, ?)
                """
                params = (coal_mark, ash_value, moisture_value, calorific_value, price_value)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_coal(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите марку угля для удаления')
            return
        
        coal_mark = self.table.item(selected_row, 0).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить марку угля "{coal_mark}"?\n'
            'Внимание: если есть записи о добыче этого угля, удаление будет невозможно.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM coal WHERE coal_mark = ?"
                self.db.execute_query(query, (coal_mark,))
                self.load_data()
                self.status_label.setText(f'Марка угля "{coal_mark}" удалена')
            except Exception as e:
                if 'FOREIGN KEY constraint failed' in str(e):
                    QMessageBox.critical(
                        self, 'Ошибка удаления',
                        f'Невозможно удалить марку угля "{coal_mark}", '
                        'так как есть записи о добыче этого угля.'
                    )
                else:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')