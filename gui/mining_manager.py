from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from database.db_connection import DatabaseConnection
from datetime import datetime

class MiningManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_mining_id = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление добычей')
        self.setMinimumSize(1000, 500)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_mining)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_mining)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_mining)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        # Фильтр по дате
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Дата', 'Смена', 'Марка угля', 'Участок', 
            'Объем добычи (т)', 'Объем породы (т)', 'Стоимость (руб)'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_mining)
        
        layout.addWidget(self.table)
        
        # Статистика
        self.stats_label = QLabel('')
        layout.addWidget(self.stats_label)
    
    def load_data(self):
        try:
            date_from = self.date_from.date().toString('yyyy-MM-dd')
            date_to = self.date_to.date().toString('yyyy-MM-dd')
            
            query = """
            SELECT m.*, s.section_name, c.coal_mark, c.price_per_ton,
                   (m.volume * c.price_per_ton) as total_cost
            FROM mining m
            JOIN sections s ON m.section_id = s.section_id
            JOIN coal c ON m.coal_mark = c.coal_mark
            WHERE m.mining_date BETWEEN ? AND ?
            ORDER BY m.mining_date DESC, m.shift
            """
            
            results = self.db.fetch_all(query, (date_from, date_to))
            
            self.table.setRowCount(len(results))
            
            total_volume = 0
            total_rock = 0
            total_cost = 0
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['mining_id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['mining_date']))
                self.table.setItem(i, 2, QTableWidgetItem(str(row['shift'])))
                self.table.setItem(i, 3, QTableWidgetItem(row['coal_mark']))
                self.table.setItem(i, 4, QTableWidgetItem(row['section_name']))
                self.table.setItem(i, 5, QTableWidgetItem(f"{row['volume']:.1f}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{row['rock_volume']:.1f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"{row['total_cost']:,.0f}"))
                
                total_volume += row['volume'] or 0
                total_rock += row['rock_volume'] or 0
                total_cost += row['total_cost'] or 0
            
            self.table.resizeColumnsToContents()
            
            # Обновляем статистику
            self.stats_label.setText(
                f'Период: {date_from} - {date_to} | '
                f'Всего добычи: {total_volume:.1f} т | '
                f'Всего породы: {total_rock:.1f} т | '
                f'Общая стоимость: {total_cost:,.0f} руб'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_mining(self):
        self.current_mining_id = None
        self.show_mining_dialog()
    
    def edit_mining(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите запись для редактирования')
            return
        
        mining_id = int(self.table.item(selected_row, 0).text())
        self.current_mining_id = mining_id
        self.show_mining_dialog()
    
    def show_mining_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование добычи' if self.current_mining_id else 'Добавление добычи')
        dialog.setMinimumSize(500, 350)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.setDisplayFormat('dd.MM.yyyy')
        
        shift_combo = QComboBox()
        shift_combo.addItems(['1', '2'])
        
        coal_combo = QComboBox()
        section_combo = QComboBox()
        
        volume_edit = QLineEdit()
        volume_edit.setValidator(QDoubleValidator(0, 100000, 2))
        
        rock_edit = QLineEdit()
        rock_edit.setValidator(QDoubleValidator(0, 100000, 2))
        
        # Загружаем списки
        try:
            query = "SELECT coal_mark FROM coal ORDER BY coal_mark"
            coals = self.db.fetch_all(query)
            for coal in coals:
                coal_combo.addItem(coal['coal_mark'])
            
            query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
            sections = self.db.fetch_all(query)
            for section in sections:
                section_combo.addItem(section['section_name'], section['section_id'])
        except Exception as e:
            print(f"Ошибка загрузки списков: {e}")
        
        # Загружаем данные для редактирования
        if self.current_mining_id:
            query = "SELECT * FROM mining WHERE mining_id = ?"
            mining_data = self.db.fetch_one(query, (self.current_mining_id,))
            
            if mining_data:
                # Дата
                try:
                    mining_date = datetime.strptime(mining_data['mining_date'], '%Y-%m-%d')
                    date_edit.setDate(QDate(mining_date.year, mining_date.month, mining_date.day))
                except:
                    pass
                
                # Смена
                shift_combo.setCurrentText(str(mining_data['shift']))
                
                # Марка угля
                for i in range(coal_combo.count()):
                    if coal_combo.itemText(i) == mining_data['coal_mark']:
                        coal_combo.setCurrentIndex(i)
                        break
                
                # Участок
                for i in range(section_combo.count()):
                    if section_combo.itemData(i) == mining_data['section_id']:
                        section_combo.setCurrentIndex(i)
                        break
                
                volume_edit.setText(str(mining_data['volume']) if mining_data['volume'] else '')
                rock_edit.setText(str(mining_data['rock_volume']) if mining_data['rock_volume'] else '')
        
        layout.addRow('Дата:', date_edit)
        layout.addRow('Смена:', shift_combo)
        layout.addRow('Марка угля:', coal_combo)
        layout.addRow('Участок:', section_combo)
        layout.addRow('Объем добычи (т):', volume_edit)
        layout.addRow('Объем породы (т):', rock_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_mining(
            dialog, date_edit.date().toString('yyyy-MM-dd'),
            shift_combo.currentText(), coal_combo.currentText(),
            section_combo.currentData(), volume_edit.text(), rock_edit.text()
        ))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_mining(self, dialog, date, shift, coal_mark, section_id, volume, rock):
        # Валидация
        if not volume.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите объем добычи')
            return
        
        try:
            volume_value = float(volume) if volume else 0
            rock_value = float(rock) if rock else 0
            shift_value = int(shift)
            
            if self.current_mining_id:
                # Обновление существующей записи
                query = """
                UPDATE mining SET 
                    mining_date = ?,
                    shift = ?,
                    coal_mark = ?,
                    section_id = ?,
                    volume = ?,
                    rock_volume = ?
                WHERE mining_id = ?
                """
                params = (date, shift_value, coal_mark, section_id, 
                         volume_value, rock_value, self.current_mining_id)
            else:
                # Добавление новой записи
                query = """
                INSERT INTO mining 
                (mining_date, shift, coal_mark, section_id, volume, rock_volume)
                VALUES (?, ?, ?, ?, ?, ?)
                """
                params = (date, shift_value, coal_mark, section_id, volume_value, rock_value)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_mining(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите запись для удаления')
            return
        
        mining_id = int(self.table.item(selected_row, 0).text())
        mining_date = self.table.item(selected_row, 1).text()
        volume = self.table.item(selected_row, 5).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить запись о добыче от {mining_date} ({volume} т)?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM mining WHERE mining_id = ?"
                self.db.execute_query(query, (mining_id,))
                self.load_data()
                self.stats_label.setText(f'Запись #{mining_id} удалена')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')