from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from database.db_connection import DatabaseConnection
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from datetime import datetime

class WorkerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Работники')
        self.setGeometry(300, 200, 900, 600)
        
        layout = QVBoxLayout(self)
        
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
        
        layout.addLayout(toolbar)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            'Таб. №', 'ФИО', 'Участок', 'Должность',
            'ИИН', 'Адрес', 'Телефон', 'Пол', 'Дата рождения'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        # Фильтры
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel('Фильтр по участку:')
        filter_layout.addWidget(filter_label)
        
        self.section_combo = QComboBox()
        self.section_combo.addItem('Все участки', None)
        self.load_sections()
        self.section_combo.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.section_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
    
    def load_sections(self):
        query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
        sections = self.db.fetch_all(query)
        
        for section_id, section_name in sections:
            self.section_combo.addItem(section_name, section_id)
    
    def load_data(self):
        try:
            section_id = self.section_combo.currentData()
            
            if section_id:
                query = """
                SELECT w.tab_number, w.full_name, s.section_name, p.position_name,
                       w.iin, w.address, w.phone, w.gender, w.birth_date
                FROM workers w
                JOIN sections s ON w.section_id = s.section_id
                JOIN positions p ON w.position_id = p.position_id
                WHERE w.section_id = %s
                ORDER BY w.tab_number
                """
                params = (section_id,)
            else:
                query = """
                SELECT w.tab_number, w.full_name, s.section_name, p.position_name,
                       w.iin, w.address, w.phone, w.gender, w.birth_date
                FROM workers w
                JOIN sections s ON w.section_id = s.section_id
                JOIN positions p ON w.position_id = p.position_id
                ORDER BY w.tab_number
                """
                params = None
            
            workers = self.db.fetch_all(query, params)
            
            self.table.setRowCount(len(workers))
            for i, worker in enumerate(workers):
                for j, value in enumerate(worker):
                    item = QTableWidgetItem(str(value) if value is not None else '')
                    self.table.setItem(i, j, item)
                    
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_worker(self):
        dialog = WorkerEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def edit_worker(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите работника для редактирования')
            return
        
        tab_number = int(self.table.item(selected, 0).text())
        
        dialog = WorkerEditDialog(self, tab_number)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def delete_worker(self):
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите работника для удаления')
            return
        
        tab_number = int(self.table.item(selected, 0).text())
        full_name = self.table.item(selected, 1).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f'Удалить работника {full_name} (таб. №{tab_number})?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM workers WHERE tab_number = %s"
                self.db.execute_query(query, (tab_number,))
                QMessageBox.information(self, 'Успех', 'Работник удален')
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')


class WorkerEditDialog(QDialog):
    def __init__(self, parent=None, tab_number=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.tab_number = tab_number
        self.is_edit = tab_number is not None
        self.init_ui()
        
    def init_ui(self):
        title = 'Редактирование работника' if self.is_edit else 'Добавление работника'
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        # Табельный номер
        self.tab_edit = QLineEdit()
        self.tab_edit.setValidator(QIntValidator(1, 999999))
        if self.is_edit:
            self.tab_edit.setText(str(self.tab_number))
            self.tab_edit.setReadOnly(True)
        layout.addRow('Табельный номер:', self.tab_edit)
        
        # ФИО
        self.name_edit = QLineEdit()
        layout.addRow('ФИО:', self.name_edit)
        
        # Участок
        self.section_combo = QComboBox()
        self.load_sections()
        layout.addRow('Участок:', self.section_combo)
        
        # Должность
        self.position_combo = QComboBox()
        self.load_positions()
        layout.addRow('Должность:', self.position_combo)
        
        # ИИН
        self.iin_edit = QLineEdit()
        self.iin_edit.setMaxLength(12)
        layout.addRow('ИИН:', self.iin_edit)
        
        # Адрес
        self.address_edit = QLineEdit()
        layout.addRow('Адрес:', self.address_edit)
        
        # Телефон
        self.phone_edit = QLineEdit()
        layout.addRow('Телефон:', self.phone_edit)
        
        # Пол
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(['М', 'Ж'])
        layout.addRow('Пол:', self.gender_combo)
        
        # Дата рождения
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setMaximumDate(datetime.today())
        layout.addRow('Дата рождения:', self.birth_date_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.save)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)
        
        # Загрузка данных для редактирования
        if self.is_edit:
            self.load_worker_data()
    
    def load_sections(self):
        query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
        sections = self.db.fetch_all(query)
        
        for section_id, section_name in sections:
            self.section_combo.addItem(section_name, section_id)
    
    def load_positions(self):
        query = "SELECT position_id, position_name FROM positions ORDER BY position_name"
        positions = self.db.fetch_all(query)
        
        for position_id, position_name in positions:
            self.position_combo.addItem(position_name, position_id)
    
    def load_worker_data(self):
        try:
            query = """
            SELECT full_name, section_id, position_id, iin, 
                   address, phone, gender, birth_date
            FROM workers WHERE tab_number = %s
            """
            worker = self.db.fetch_one(query, (self.tab_number,))
            
            if worker:
                self.name_edit.setText(worker[0])
                
                # Устанавливаем участок
                for i in range(self.section_combo.count()):
                    if self.section_combo.itemData(i) == worker[1]:
                        self.section_combo.setCurrentIndex(i)
                        break
                
                # Устанавливаем должность
                for i in range(self.position_combo.count()):
                    if self.position_combo.itemData(i) == worker[2]:
                        self.position_combo.setCurrentIndex(i)
                        break
                
                self.iin_edit.setText(worker[3])
                self.address_edit.setText(worker[4] if worker[4] else '')
                self.phone_edit.setText(worker[5] if worker[5] else '')
                
                # Пол
                if worker[6] == 'М':
                    self.gender_combo.setCurrentIndex(0)
                else:
                    self.gender_combo.setCurrentIndex(1)
                
                # Дата рождения
                if worker[7]:
                    date = datetime.strptime(str(worker[7]), '%Y-%m-%d')
                    self.birth_date_edit.setDate(date)
                    
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def save(self):

        # Валидация
        if not self.tab_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Введите табельный номер')
            return
        
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Введите ФИО')
            return
        
        if not self.iin_edit.text().strip():
            QMessageBox.warning(self, 'Ошибка', 'Введите ИИН')
            return
        
        try:
            tab_number = int(self.tab_edit.text())
            section_id = self.section_combo.currentData()
            position_id = self.position_combo.currentData()
            birth_date = self.birth_date_edit.date().toPyDate()
            
            if self.is_edit:
                # Обновление
                query = """
                UPDATE workers SET 
                    full_name = %s,
                    section_id = %s,
                    position_id = %s,
                    iin = %s,
                    address = %s,
                    phone = %s,
                    gender = %s,
                    birth_date = %s
                WHERE tab_number = %s
                """
                params = (
                    self.name_edit.text(),
                    section_id,
                    position_id,
                    self.iin_edit.text(),
                    self.address_edit.text(),
                    self.phone_edit.text(),
                    self.gender_combo.currentText(),
                    birth_date,
                    tab_number
                )
            else:
                # Добавление
                query = """
                INSERT INTO workers 
                (tab_number, full_name, section_id, position_id, iin, 
                 address, phone, gender, birth_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    tab_number,
                    self.name_edit.text(),
                    section_id,
                    position_id,
                    self.iin_edit.text(),
                    self.address_edit.text(),
                    self.phone_edit.text(),
                    self.gender_combo.currentText(),
                    birth_date
                )
            
            self.db.execute_query(query, params)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка сохранения: {str(e)}')