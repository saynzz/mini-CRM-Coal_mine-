from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from database.db_connection import DatabaseConnection
from datetime import datetime

class WorkerManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_tab_number = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление работниками')
        self.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_worker)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_worker)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_worker)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        # Фильтр по участку
        toolbar.addWidget(QLabel('Фильтр по участку:'))
        self.filter_combo = QComboBox()
        self.filter_combo.addItem('Все участки', None)
        self.load_sections_filter()
        self.filter_combo.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.filter_combo)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Таб.№', 'ФИО', 'Участок', 'Должность', 
            'ИИН', 'Телефон', 'Пол', 'Дата рождения', 'Адрес'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_worker)
        
        layout.addWidget(self.table)
        
        # Статус
        self.status_label = QLabel('Готово')
        layout.addWidget(self.status_label)
    
    def load_sections_filter(self):
        try:
            query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
            sections = self.db.fetch_all(query)
            
            for section in sections:
                self.filter_combo.addItem(section['section_name'], section['section_id'])
        except Exception as e:
            print(f"Ошибка загрузки участков: {e}")
    
    def load_data(self):
        try:
            section_id = self.filter_combo.currentData()
            
            if section_id:
                query = """
                SELECT w.*, s.section_name, p.position_name
                FROM workers w
                JOIN sections s ON w.section_id = s.section_id
                JOIN positions p ON w.position_id = p.position_id
                WHERE w.section_id = ?
                ORDER BY w.full_name
                """
                params = (section_id,)
            else:
                query = """
                SELECT w.*, s.section_name, p.position_name
                FROM workers w
                JOIN sections s ON w.section_id = s.section_id
                JOIN positions p ON w.position_id = p.position_id
                ORDER BY w.full_name
                """
                params = None
            
            results = self.db.fetch_all(query, params)
            
            self.table.setRowCount(len(results))
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['tab_number'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['full_name']))
                self.table.setItem(i, 2, QTableWidgetItem(row['section_name']))
                self.table.setItem(i, 3, QTableWidgetItem(row['position_name']))
                self.table.setItem(i, 4, QTableWidgetItem(row['iin']))
                self.table.setItem(i, 5, QTableWidgetItem(row['phone'] if row['phone'] else ''))
                self.table.setItem(i, 6, QTableWidgetItem(row['gender']))
                self.table.setItem(i, 7, QTableWidgetItem(row['birth_date'] if row['birth_date'] else ''))
                self.table.setItem(i, 8, QTableWidgetItem(row['address'] if row['address'] else ''))
            
            self.table.resizeColumnsToContents()
            self.status_label.setText(f'Загружено работников: {len(results)}')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_worker(self):
        self.current_tab_number = None
        self.show_worker_dialog()
    
    def edit_worker(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите работника для редактирования')
            return
        
        tab_number = int(self.table.item(selected_row, 0).text())
        self.current_tab_number = tab_number
        self.show_worker_dialog()
    
    def show_worker_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование работника' if self.current_tab_number else 'Добавление работника')
        dialog.setMinimumSize(500, 400)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        tab_edit = QLineEdit()
        tab_edit.setValidator(QIntValidator(1, 999999))
        if self.current_tab_number:
            tab_edit.setText(str(self.current_tab_number))
            tab_edit.setReadOnly(True)
        
        name_edit = QLineEdit()
        
        # Комбобоксы
        section_combo = QComboBox()
        position_combo = QComboBox()
        
        iin_edit = QLineEdit()
        iin_edit.setMaxLength(12)
        
        address_edit = QLineEdit()
        phone_edit = QLineEdit()
        
        gender_combo = QComboBox()
        gender_combo.addItems(['М', 'Ж'])
        
        birth_date_edit = QDateEdit()
        birth_date_edit.setCalendarPopup(True)
        birth_date_edit.setMaximumDate(QDate.currentDate())
        birth_date_edit.setDisplayFormat('dd.MM.yyyy')
        
        # Загружаем списки участков и должностей
        try:
            query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
            sections = self.db.fetch_all(query)
            for section in sections:
                section_combo.addItem(section['section_name'], section['section_id'])
            
            query = "SELECT position_id, position_name FROM positions ORDER BY position_name"
            positions = self.db.fetch_all(query)
            for position in positions:
                position_combo.addItem(position['position_name'], position['position_id'])
        except Exception as e:
            print(f"Ошибка загрузки списков: {e}")
        
        # Загружаем данные для редактирования
        if self.current_tab_number:
            query = """
            SELECT * FROM workers 
            WHERE tab_number = ?
            """
            worker_data = self.db.fetch_one(query, (self.current_tab_number,))
            
            if worker_data:
                name_edit.setText(worker_data['full_name'])
                
                # Устанавливаем участок
                for i in range(section_combo.count()):
                    if section_combo.itemData(i) == worker_data['section_id']:
                        section_combo.setCurrentIndex(i)
                        break
                
                # Устанавливаем должность
                for i in range(position_combo.count()):
                    if position_combo.itemData(i) == worker_data['position_id']:
                        position_combo.setCurrentIndex(i)
                        break
                
                iin_edit.setText(worker_data['iin'])
                address_edit.setText(worker_data['address'] if worker_data['address'] else '')
                phone_edit.setText(worker_data['phone'] if worker_data['phone'] else '')
                
                # Пол
                if worker_data['gender'] == 'М':
                    gender_combo.setCurrentIndex(0)
                else:
                    gender_combo.setCurrentIndex(1)
                
                # Дата рождения
                if worker_data['birth_date']:
                    try:
                        birth_date = datetime.strptime(worker_data['birth_date'], '%Y-%m-%d')
                        birth_date_edit.setDate(QDate(birth_date.year, birth_date.month, birth_date.day))
                    except:
                        pass
        
        layout.addRow('Табельный номер:', tab_edit)
        layout.addRow('ФИО:', name_edit)
        layout.addRow('Участок:', section_combo)
        layout.addRow('Должность:', position_combo)
        layout.addRow('ИИН:', iin_edit)
        layout.addRow('Адрес:', address_edit)
        layout.addRow('Телефон:', phone_edit)
        layout.addRow('Пол:', gender_combo)
        layout.addRow('Дата рождения:', birth_date_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_worker(
            dialog, 
            tab_edit.text(), name_edit.text(),
            section_combo.currentData(), position_combo.currentData(),
            iin_edit.text(), address_edit.text(), phone_edit.text(),
            gender_combo.currentText(), birth_date_edit.date().toString('yyyy-MM-dd')
        ))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_worker(self, dialog, tab_number, name, section_id, position_id, 
                   iin, address, phone, gender, birth_date):
        # Валидация
        if not tab_number.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите табельный номер')
            return
        
        if not name.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите ФИО')
            return
        
        if not iin.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите ИИН')
            return
        
        try:
            tab_num = int(tab_number)
            
            if self.current_tab_number:
                # Обновление существующего работника
                query = """
                UPDATE workers SET 
                    full_name = ?,
                    section_id = ?,
                    position_id = ?,
                    iin = ?,
                    address = ?,
                    phone = ?,
                    gender = ?,
                    birth_date = ?
                WHERE tab_number = ?
                """
                params = (name, section_id, position_id, iin, 
                         address, phone, gender, birth_date if birth_date != '2000-01-01' else None, 
                         tab_num)
            else:
                # Добавление нового работника
                query = """
                INSERT INTO workers 
                (tab_number, full_name, section_id, position_id, iin, 
                 address, phone, gender, birth_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (tab_num, name, section_id, position_id, iin,
                         address, phone, gender, birth_date if birth_date != '2000-01-01' else None)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_worker(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите работника для удаления')
            return
        
        tab_number = int(self.table.item(selected_row, 0).text())
        full_name = self.table.item(selected_row, 1).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить работника {full_name} (таб.№{tab_number})?\n'
            'Внимание: если работник является руководителем участка или есть связанные данные, удаление будет невозможно.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM workers WHERE tab_number = ?"
                self.db.execute_query(query, (tab_number,))
                self.load_data()
                self.status_label.setText(f'Работник {full_name} удален')
            except Exception as e:
                if 'FOREIGN KEY constraint failed' in str(e):
                    QMessageBox.critical(
                        self, 'Ошибка удаления',
                        f'Невозможно удалить работника {full_name}, '
                        'так как он является руководителем участка или есть связанные данные.'
                    )
                else:
                    QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')