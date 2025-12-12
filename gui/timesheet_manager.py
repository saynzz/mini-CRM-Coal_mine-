from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
from database.db_connection import DatabaseConnection
from datetime import datetime

class TimesheetManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Учет рабочего времени')
        self.setMinimumSize(900, 500)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_timesheet)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_timesheet)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_timesheet)
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
            'Дата', 'Смена', 'Участок', 'Таб.№', 
            'ФИО', 'Должность', 'Отработано часов'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_timesheet)
        
        layout.addWidget(self.table)
        
        # Статистика
        self.stats_label = QLabel('')
        layout.addWidget(self.stats_label)
    
    def load_data(self):
        try:
            date_from = self.date_from.date().toString('yyyy-MM-dd')
            date_to = self.date_to.date().toString('yyyy-MM-dd')
            
            query = """
            SELECT t.*, s.section_name, w.full_name, p.position_name
            FROM time_sheet t
            JOIN workers w ON t.tab_number = w.tab_number
            JOIN sections s ON t.section_id = s.section_id
            JOIN positions p ON w.position_id = p.position_id
            WHERE t.date BETWEEN ? AND ?
            ORDER BY t.date DESC, t.shift, w.full_name
            """
            
            results = self.db.fetch_all(query, (date_from, date_to))
            
            self.table.setRowCount(len(results))
            
            total_hours = 0
            worker_count = len(set([r['tab_number'] for r in results]))
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(row['date']))
                self.table.setItem(i, 1, QTableWidgetItem(str(row['shift'])))
                self.table.setItem(i, 2, QTableWidgetItem(row['section_name']))
                self.table.setItem(i, 3, QTableWidgetItem(str(row['tab_number'])))
                self.table.setItem(i, 4, QTableWidgetItem(row['full_name']))
                self.table.setItem(i, 5, QTableWidgetItem(row['position_name']))
                self.table.setItem(i, 6, QTableWidgetItem(f"{row['hours']:.1f}"))
                
                total_hours += row['hours'] or 0
            
            self.table.resizeColumnsToContents()
            
            # Обновляем статистику
            self.stats_label.setText(
                f'Период: {date_from} - {date_to} | '
                f'Работников: {worker_count} | '
                f'Всего часов: {total_hours:.1f} | '
                f'Средне за день: {total_hours / max(1, len(results)):.1f} ч/чел'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_timesheet(self):
        self.show_timesheet_dialog()
    
    def edit_timesheet(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите запись для редактирования')
            return
        
        date = self.table.item(selected_row, 0).text()
        shift = int(self.table.item(selected_row, 1).text())
        tab_number = int(self.table.item(selected_row, 3).text())
        
        self.show_timesheet_dialog(date, shift, tab_number)
    
    def show_timesheet_dialog(self, date=None, shift=None, tab_number=None):
        dialog = QDialog(self)
        is_edit = date is not None
        dialog.setWindowTitle('Редактирование учета времени' if is_edit else 'Добавление учета времени')
        dialog.setMinimumSize(500, 300)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate() if not date else QDate.fromString(date, 'yyyy-MM-dd'))
        date_edit.setDisplayFormat('dd.MM.yyyy')
        
        shift_combo = QComboBox()
        shift_combo.addItems(['1', '2'])
        if shift:
            shift_combo.setCurrentText(str(shift))
        
        worker_combo = QComboBox()
        hours_edit = QLineEdit()
        hours_edit.setValidator(QDoubleValidator(0, 12, 1))
        
        # Загружаем список работников
        try:
            query = """
            SELECT w.tab_number, w.full_name, s.section_name
            FROM workers w
            JOIN sections s ON w.section_id = s.section_id
            ORDER BY w.full_name
            """
            workers = self.db.fetch_all(query)
            for worker in workers:
                worker_combo.addItem(
                    f"{worker['tab_number']} - {worker['full_name']} ({worker['section_name']})",
                    worker['tab_number']
                )
        except Exception as e:
            print(f"Ошибка загрузки работников: {e}")
        
        # Загружаем данные для редактирования
        if is_edit and date and shift and tab_number:
            query = """
            SELECT t.*, w.full_name
            FROM time_sheet t
            JOIN workers w ON t.tab_number = w.tab_number
            WHERE t.date = ? AND t.shift = ? AND t.tab_number = ?
            """
            timesheet_data = self.db.fetch_one(query, (date, shift, tab_number))
            
            if timesheet_data:
                # Устанавливаем работника
                for i in range(worker_combo.count()):
                    if worker_combo.itemData(i) == tab_number:
                        worker_combo.setCurrentIndex(i)
                        break
                
                hours_edit.setText(str(timesheet_data['hours']))
        
        layout.addRow('Дата:', date_edit)
        layout.addRow('Смена:', shift_combo)
        layout.addRow('Работник:', worker_combo)
        layout.addRow('Отработано часов:', hours_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        if is_edit:
            btn_box.accepted.connect(lambda: self.update_timesheet(
                dialog, date, shift, tab_number,
                date_edit.date().toString('yyyy-MM-dd'),
                shift_combo.currentText(), worker_combo.currentData(),
                hours_edit.text()
            ))
        else:
            btn_box.accepted.connect(lambda: self.save_timesheet(
                dialog, date_edit.date().toString('yyyy-MM-dd'),
                shift_combo.currentText(), worker_combo.currentData(),
                hours_edit.text()
            ))
        
        btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_timesheet(self, dialog, date, shift, tab_number, hours):
        if not hours.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите количество часов')
            return
        
        try:
            # Получаем section_id работника
            query = "SELECT section_id FROM workers WHERE tab_number = ?"
            worker = self.db.fetch_one(query, (tab_number,))
            
            if not worker:
                QMessageBox.warning(dialog, 'Ошибка', 'Работник не найден')
                return
            
            section_id = worker['section_id']
            hours_value = float(hours)
            shift_value = int(shift)
            
            # Проверяем, нет ли уже записи на эту дату и смену
            check_query = """
            SELECT COUNT(*) as count FROM time_sheet 
            WHERE date = ? AND shift = ? AND tab_number = ?
            """
            check_result = self.db.fetch_one(check_query, (date, shift_value, tab_number))
            
            if check_result['count'] > 0:
                QMessageBox.warning(dialog, 'Ошибка', 'Уже есть запись для этого работника на эту дату и смену')
                return
            
            # Добавляем запись
            query = """
            INSERT INTO time_sheet 
            (date, section_id, shift, tab_number, hours)
            VALUES (?, ?, ?, ?, ?)
            """
            params = (date, section_id, shift_value, tab_number, hours_value)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def update_timesheet(self, dialog, old_date, old_shift, old_tab_number, 
                        new_date, new_shift, new_tab_number, hours):
        if not hours.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите количество часов')
            return
        
        try:
            hours_value = float(hours)
            shift_value = int(new_shift)
            
            # Если изменился работник, получаем новый section_id
            if old_tab_number != new_tab_number:
                query = "SELECT section_id FROM workers WHERE tab_number = ?"
                worker = self.db.fetch_one(query, (new_tab_number,))
                
                if not worker:
                    QMessageBox.warning(dialog, 'Ошибка', 'Работник не найден')
                    return
                
                section_id = worker['section_id']
            else:
                # Иначе используем старый section_id
                query = "SELECT section_id FROM time_sheet WHERE date = ? AND shift = ? AND tab_number = ?"
                old_record = self.db.fetch_one(query, (old_date, int(old_shift), old_tab_number))
                section_id = old_record['section_id']
            
            # Обновляем запись
            query = """
            UPDATE time_sheet SET 
                date = ?,
                section_id = ?,
                shift = ?,
                tab_number = ?,
                hours = ?
            WHERE date = ? AND shift = ? AND tab_number = ?
            """
            params = (new_date, section_id, shift_value, new_tab_number, hours_value,
                     old_date, int(old_shift), old_tab_number)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_timesheet(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите запись для удаления')
            return
        
        date = self.table.item(selected_row, 0).text()
        shift = int(self.table.item(selected_row, 1).text())
        worker_name = self.table.item(selected_row, 4).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить запись учета времени для {worker_name} от {date} (смена {shift})?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = """
                DELETE FROM time_sheet 
                WHERE date = ? AND shift = ? AND tab_number = (
                    SELECT tab_number FROM workers WHERE full_name = ?
                )
                """
                self.db.execute_query(query, (date, shift, worker_name))
                self.load_data()
                self.stats_label.setText(f'Запись для {worker_name} удалена')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')