from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from database.db_connection import DatabaseConnection
from datetime import datetime

class CostManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_cost_id = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление затратами')
        self.setMinimumSize(900, 500)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_cost)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_cost)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_cost)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        # Фильтр
        toolbar.addWidget(QLabel('Период:'))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setDisplayFormat('dd.MM.yyyy')
        toolbar.addWidget(self.date_from)
        
        toolbar.addWidget(QLabel('-'))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat('dd.MM.yyyy')
        toolbar.addWidget(self.date_to)
        
        filter_btn = QPushButton('Фильтровать')
        filter_btn.clicked.connect(self.load_data)
        toolbar.addWidget(filter_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Дата', 'Смена', 'Участок', 
            'Электроэнергия (кВт·ч)', 'Топливо (л)', 'Общая стоимость'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_cost)
        
        layout.addWidget(self.table)
        
        # Статистика
        self.stats_label = QLabel('')
        layout.addWidget(self.stats_label)
    
    def load_data(self):
        try:
            date_from = self.date_from.date().toString('yyyy-MM-dd')
            date_to = self.date_to.date().toString('yyyy-MM-dd')
            
            query = """
            SELECT c.*, s.section_name,
                   (c.electricity * 5.5 + c.fuel * 55) as total_cost
            FROM costs c
            JOIN sections s ON c.section_id = s.section_id
            WHERE c.cost_date BETWEEN ? AND ?
            ORDER BY c.cost_date DESC, c.shift
            """
            
            results = self.db.fetch_all(query, (date_from, date_to))
            
            self.table.setRowCount(len(results))
            
            total_electricity = 0
            total_fuel = 0
            total_cost = 0
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['cost_id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['cost_date']))
                self.table.setItem(i, 2, QTableWidgetItem(str(row['shift'])))
                self.table.setItem(i, 3, QTableWidgetItem(row['section_name']))
                self.table.setItem(i, 4, QTableWidgetItem(f"{row['electricity']:.1f}" if row['electricity'] else '0.0'))
                self.table.setItem(i, 5, QTableWidgetItem(f"{row['fuel']:.1f}" if row['fuel'] else '0.0'))
                self.table.setItem(i, 6, QTableWidgetItem(f"{row['total_cost']:,.0f}" if row['total_cost'] else '0'))
                
                total_electricity += row['electricity'] or 0
                total_fuel += row['fuel'] or 0
                total_cost += row['total_cost'] or 0
            
            self.table.resizeColumnsToContents()
            
            # Обновляем статистику
            self.stats_label.setText(
                f'Период: {date_from} - {date_to} | '
                f'Электроэнергия: {total_electricity:.1f} кВт·ч | '
                f'Топливо: {total_fuel:.1f} л | '
                f'Общая стоимость: {total_cost:,.0f} руб'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_cost(self):
        self.current_cost_id = None
        self.show_cost_dialog()
    
    def edit_cost(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите запись для редактирования')
            return
        
        cost_id = int(self.table.item(selected_row, 0).text())
        self.current_cost_id = cost_id
        self.show_cost_dialog()
    
    def show_cost_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование затрат' if self.current_cost_id else 'Добавление затрат')
        dialog.setMinimumSize(400, 300)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat('dd.MM.yyyy')
        
        shift_combo = QComboBox()
        shift_combo.addItems(['1', '2'])
        
        section_combo = QComboBox()
        
        electricity_edit = QLineEdit()
        electricity_edit.setValidator(QDoubleValidator(0, 100000, 2))
        
        fuel_edit = QLineEdit()
        fuel_edit.setValidator(QDoubleValidator(0, 100000, 2))
        
        # Загружаем список участков
        try:
            query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
            sections = self.db.fetch_all(query)
            for section in sections:
                section_combo.addItem(section['section_name'], section['section_id'])
        except Exception as e:
            print(f"Ошибка загрузки участков: {e}")
        
        # Загружаем данные для редактирования
        if self.current_cost_id:
            query = "SELECT * FROM costs WHERE cost_id = ?"
            cost_data = self.db.fetch_one(query, (self.current_cost_id,))
            
            if cost_data:
                # Дата
                try:
                    cost_date = datetime.strptime(cost_data['cost_date'], '%Y-%m-%d')
                    date_edit.setDate(QDate(cost_date.year, cost_date.month, cost_date.day))
                except:
                    pass
                
                # Смена
                shift_combo.setCurrentText(str(cost_data['shift']))
                
                # Участок
                for i in range(section_combo.count()):
                    if section_combo.itemData(i) == cost_data['section_id']:
                        section_combo.setCurrentIndex(i)
                        break
                
                electricity_edit.setText(str(cost_data['electricity']) if cost_data['electricity'] else '')
                fuel_edit.setText(str(cost_data['fuel']) if cost_data['fuel'] else '')
        
        layout.addRow('Дата:', date_edit)
        layout.addRow('Смена:', shift_combo)
        layout.addRow('Участок:', section_combo)
        layout.addRow('Электроэнергия (кВт·ч):', electricity_edit)
        layout.addRow('Топливо (л):', fuel_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_cost(
            dialog, date_edit.date().toString('yyyy-MM-dd'),
            shift_combo.currentText(), section_combo.currentData(),
            electricity_edit.text(), fuel_edit.text()
        ))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_cost(self, dialog, date, shift, section_id, electricity, fuel):
        # Валидация
        if not electricity.strip() and not fuel.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите хотя бы один вид затрат')
            return
        
        try:
            electricity_value = float(electricity) if electricity else 0
            fuel_value = float(fuel) if fuel else 0
            shift_value = int(shift)
            
            if self.current_cost_id:
                # Обновление существующей записи
                query = """
                UPDATE costs SET 
                    cost_date = ?,
                    shift = ?,
                    section_id = ?,
                    electricity = ?,
                    fuel = ?
                WHERE cost_id = ?
                """
                params = (date, shift_value, section_id, 
                         electricity_value, fuel_value, self.current_cost_id)
            else:
                # Добавление новой записи
                query = """
                INSERT INTO costs 
                (cost_date, shift, section_id, electricity, fuel)
                VALUES (?, ?, ?, ?, ?)
                """
                params = (date, shift_value, section_id, electricity_value, fuel_value)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_cost(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите запись для удаления')
            return
        
        cost_id = int(self.table.item(selected_row, 0).text())
        cost_date = self.table.item(selected_row, 1).text()
        section = self.table.item(selected_row, 3).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить запись о затратах от {cost_date} ({section})?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM costs WHERE cost_id = ?"
                self.db.execute_query(query, (cost_id,))
                self.load_data()
                self.stats_label.setText(f'Запись #{cost_id} удалена')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')