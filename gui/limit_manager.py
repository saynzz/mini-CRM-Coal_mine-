from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from database.db_connection import DatabaseConnection

class LimitManager(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseConnection()
        self.current_limit_id = None
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        self.setWindowTitle('Управление лимитами')
        self.setMinimumSize(1000, 500)
        
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.add_limit)
        toolbar.addWidget(add_btn)
        
        edit_btn = QPushButton('Редактировать')
        edit_btn.clicked.connect(self.edit_limit)
        toolbar.addWidget(edit_btn)
        
        delete_btn = QPushButton('Удалить')
        delete_btn.clicked.connect(self.delete_limit)
        toolbar.addWidget(delete_btn)
        
        refresh_btn = QPushButton('Обновить')
        refresh_btn.clicked.connect(self.load_data)
        toolbar.addWidget(refresh_btn)
        
        recalc_btn = QPushButton('Пересчитать факты')
        recalc_btn.clicked.connect(self.recalculate_facts)
        toolbar.addWidget(recalc_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            'ID', 'Участок', 'Месяц', 'Год', 
            'План добычи', 'Факт добычи', '%', 
            'План породы', 'Факт породы', '%',
            'План э/энергии', 'Факт э/энергии', '%'
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.edit_limit)
        
        layout.addWidget(self.table)
        
        # Статистика
        self.stats_label = QLabel('')
        layout.addWidget(self.stats_label)
    
    def load_data(self):
        try:
            query = """
            SELECT l.*, s.section_name,
                   CASE 
                       WHEN l.plan_production > 0 
                       THEN ROUND((l.actual_production * 100.0 / l.plan_production), 2)
                       ELSE 0 
                   END as production_percent,
                   CASE 
                       WHEN l.plan_rock > 0 
                       THEN ROUND((l.actual_rock * 100.0 / l.plan_rock), 2)
                       ELSE 0 
                   END as rock_percent,
                   CASE 
                       WHEN l.plan_electricity > 0 
                       THEN ROUND((l.actual_electricity * 100.0 / l.plan_electricity), 2)
                       ELSE 0 
                   END as electricity_percent
            FROM limits l
            JOIN sections s ON l.section_id = s.section_id
            ORDER BY l.year DESC, l.month DESC, s.section_name
            """
            
            results = self.db.fetch_all(query)
            
            self.table.setRowCount(len(results))
            
            total_plan_production = 0
            total_actual_production = 0
            total_plan_rock = 0
            total_actual_rock = 0
            
            for i, row in enumerate(results):
                self.table.setItem(i, 0, QTableWidgetItem(str(row['limit_id'])))
                self.table.setItem(i, 1, QTableWidgetItem(row['section_name']))
                self.table.setItem(i, 2, QTableWidgetItem(str(row['month'])))
                self.table.setItem(i, 3, QTableWidgetItem(str(row['year'])))
                self.table.setItem(i, 4, QTableWidgetItem(f"{row['plan_production']:,.0f}" if row['plan_production'] else '0'))
                self.table.setItem(i, 5, QTableWidgetItem(f"{row['actual_production']:,.0f}" if row['actual_production'] else '0'))
                
                # Процент выполнения добычи
                percent_item = QTableWidgetItem(f"{row['production_percent']:.1f}%")
                if row['production_percent'] < 80:
                    percent_item.setBackground(Qt.red)
                    percent_item.setForeground(Qt.white)
                elif row['production_percent'] < 100:
                    percent_item.setBackground(Qt.yellow)
                else:
                    percent_item.setBackground(Qt.green)
                    percent_item.setForeground(Qt.white)
                self.table.setItem(i, 6, percent_item)
                
                self.table.setItem(i, 7, QTableWidgetItem(f"{row['plan_rock']:,.0f}" if row['plan_rock'] else '0'))
                self.table.setItem(i, 8, QTableWidgetItem(f"{row['actual_rock']:,.0f}" if row['actual_rock'] else '0'))
                
                # Процент выполнения породы
                rock_percent_item = QTableWidgetItem(f"{row['rock_percent']:.1f}%")
                if row['rock_percent'] > 120:
                    rock_percent_item.setBackground(Qt.red)
                    rock_percent_item.setForeground(Qt.white)
                elif row['rock_percent'] > 100:
                    rock_percent_item.setBackground(Qt.yellow)
                else:
                    rock_percent_item.setBackground(Qt.green)
                    rock_percent_item.setForeground(Qt.white)
                self.table.setItem(i, 9, rock_percent_item)
                
                self.table.setItem(i, 10, QTableWidgetItem(f"{row['plan_electricity']:,.0f}" if row['plan_electricity'] else '0'))
                self.table.setItem(i, 11, QTableWidgetItem(f"{row['actual_electricity']:,.0f}" if row['actual_electricity'] else '0'))
                
                # Процент выполнения электроэнергии
                elec_percent_item = QTableWidgetItem(f"{row['electricity_percent']:.1f}%")
                if row['electricity_percent'] > 120:
                    elec_percent_item.setBackground(Qt.red)
                    elec_percent_item.setForeground(Qt.white)
                elif row['electricity_percent'] > 100:
                    elec_percent_item.setBackground(Qt.yellow)
                else:
                    elec_percent_item.setBackground(Qt.green)
                    elec_percent_item.setForeground(Qt.white)
                self.table.setItem(i, 12, elec_percent_item)
                
                total_plan_production += row['plan_production'] or 0
                total_actual_production += row['actual_production'] or 0
                total_plan_rock += row['plan_rock'] or 0
                total_actual_rock += row['actual_rock'] or 0
            
            self.table.resizeColumnsToContents()
            
            # Обновляем статистику
            total_production_percent = (total_actual_production / total_plan_production * 100) if total_plan_production > 0 else 0
            total_rock_percent = (total_actual_rock / total_plan_rock * 100) if total_plan_rock > 0 else 0
            
            self.stats_label.setText(
                f'Всего планов: {len(results)} | '
                f'Добыча: {total_actual_production:,.0f}/{total_plan_production:,.0f} т ({total_production_percent:.1f}%) | '
                f'Порода: {total_actual_rock:,.0f}/{total_plan_rock:,.0f} т ({total_rock_percent:.1f}%)'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
    
    def add_limit(self):
        self.current_limit_id = None
        self.show_limit_dialog()
    
    def edit_limit(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите лимит для редактирования')
            return
        
        limit_id = int(self.table.item(selected_row, 0).text())
        self.current_limit_id = limit_id
        self.show_limit_dialog()
    
    def show_limit_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование лимита' if self.current_limit_id else 'Добавление лимита')
        dialog.setMinimumSize(500, 400)
        
        layout = QFormLayout(dialog)
        
        # Поля ввода
        section_combo = QComboBox()
        month_combo = QComboBox()
        year_edit = QLineEdit()
        
        production_edit = QLineEdit()
        production_edit.setValidator(QDoubleValidator(0, 1000000, 2))
        
        rock_edit = QLineEdit()
        rock_edit.setValidator(QDoubleValidator(0, 1000000, 2))
        
        electricity_edit = QLineEdit()
        electricity_edit.setValidator(QDoubleValidator(0, 1000000, 2))
        
        fuel_edit = QLineEdit()
        fuel_edit.setValidator(QDoubleValidator(0, 1000000, 2))
        
        # Заполняем списки
        months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        for i, month in enumerate(months, 1):
            month_combo.addItem(month, i)
        
        # Загружаем участки
        try:
            query = "SELECT section_id, section_name FROM sections ORDER BY section_name"
            sections = self.db.fetch_all(query)
            for section in sections:
                section_combo.addItem(section['section_name'], section['section_id'])
        except Exception as e:
            print(f"Ошибка загрузки участков: {e}")
        
        year_edit.setValidator(QIntValidator(2000, 2100))
        from datetime import datetime
        year_edit.setText(str(datetime.now().year))
        
        # Загружаем данные для редактирования
        if self.current_limit_id:
            query = "SELECT * FROM limits WHERE limit_id = ?"
            limit_data = self.db.fetch_one(query, (self.current_limit_id,))
            
            if limit_data:
                # Участок
                for i in range(section_combo.count()):
                    if section_combo.itemData(i) == limit_data['section_id']:
                        section_combo.setCurrentIndex(i)
                        break
                
                # Месяц
                month_combo.setCurrentIndex(limit_data['month'] - 1)
                
                year_edit.setText(str(limit_data['year']))
                production_edit.setText(str(limit_data['plan_production']) if limit_data['plan_production'] else '')
                rock_edit.setText(str(limit_data['plan_rock']) if limit_data['plan_rock'] else '')
                electricity_edit.setText(str(limit_data['plan_electricity']) if limit_data['plan_electricity'] else '')
                fuel_edit.setText(str(limit_data['plan_fuel']) if limit_data['plan_fuel'] else '')
        
        layout.addRow('Участок:', section_combo)
        layout.addRow('Месяц:', month_combo)
        layout.addRow('Год:', year_edit)
        layout.addRow('План добычи (т):', production_edit)
        layout.addRow('План породы (т):', rock_edit)
        layout.addRow('План электроэнергии (кВт·ч):', electricity_edit)
        layout.addRow('План топлива (л):', fuel_edit)
        
        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(lambda: self.save_limit(
            dialog, section_combo.currentData(), month_combo.currentData(),
            year_edit.text(), production_edit.text(), rock_edit.text(),
            electricity_edit.text(), fuel_edit.text()
        ))
        btn_box.rejected.connect(dialog.reject)
        
        layout.addRow(btn_box)
        dialog.exec_()
    
    def save_limit(self, dialog, section_id, month, year, production, rock, electricity, fuel):
        if not year.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите год')
            return
        
        if not production.strip() and not rock.strip() and not electricity.strip() and not fuel.strip():
            QMessageBox.warning(dialog, 'Ошибка', 'Введите хотя бы один плановый показатель')
            return
        
        try:
            year_value = int(year)
            month_value = int(month)
            production_value = float(production) if production else None
            rock_value = float(rock) if rock else None
            electricity_value = float(electricity) if electricity else None
            fuel_value = float(fuel) if fuel else None
            
            # Проверяем, нет ли уже лимита для этого участка на этот месяц и год
            check_query = """
            SELECT limit_id FROM limits 
            WHERE section_id = ? AND month = ? AND year = ?
            """
            check_params = (section_id, month_value, year_value)
            
            if self.current_limit_id:
                check_query += " AND limit_id != ?"
                check_params = (section_id, month_value, year_value, self.current_limit_id)
            
            existing = self.db.fetch_one(check_query, check_params)
            
            if existing:
                QMessageBox.warning(dialog, 'Ошибка', 
                    'Для этого участка уже установлен лимит на указанный месяц и год')
                return
            
            if self.current_limit_id:
                # Обновление существующего лимита
                query = """
                UPDATE limits SET 
                    section_id = ?,
                    month = ?,
                    year = ?,
                    plan_production = ?,
                    plan_rock = ?,
                    plan_electricity = ?,
                    plan_fuel = ?
                WHERE limit_id = ?
                """
                params = (section_id, month_value, year_value, production_value,
                         rock_value, electricity_value, fuel_value, self.current_limit_id)
            else:
                # Добавление нового лимита
                query = """
                INSERT INTO limits 
                (section_id, month, year, plan_production, plan_rock, 
                 plan_electricity, plan_fuel)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                params = (section_id, month_value, year_value, production_value,
                         rock_value, electricity_value, fuel_value)
            
            self.db.execute_query(query, params)
            dialog.accept()
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(dialog, 'Ошибка', f'Ошибка сохранения: {str(e)}')
    
    def delete_limit(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите лимит для удаления')
            return
        
        limit_id = int(self.table.item(selected_row, 0).text())
        section_name = self.table.item(selected_row, 1).text()
        month = self.table.item(selected_row, 2).text()
        year = self.table.item(selected_row, 3).text()
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Удалить лимит для участка "{section_name}" на {month}/{year}?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                query = "DELETE FROM limits WHERE limit_id = ?"
                self.db.execute_query(query, (limit_id,))
                self.load_data()
                self.stats_label.setText(f'Лимит для {section_name} удален')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка удаления: {str(e)}')
    
    def recalculate_facts(self):
        try:
            # Обновляем фактические данные добычи и породы
            update_query = """
            UPDATE limits 
            SET actual_production = COALESCE((
                SELECT SUM(volume) 
                FROM mining 
                WHERE mining.section_id = limits.section_id
                  AND strftime('%m', mining.mining_date) = printf('%02d', limits.month)
                  AND strftime('%Y', mining.mining_date) = printf('%d', limits.year)
            ), 0),
            actual_rock = COALESCE((
                SELECT SUM(rock_volume) 
                FROM mining 
                WHERE mining.section_id = limits.section_id
                  AND strftime('%m', mining.mining_date) = printf('%02d', limits.month)
                  AND strftime('%Y', mining.mining_date) = printf('%d', limits.year)
            ), 0),
            actual_electricity = COALESCE((
                SELECT SUM(electricity) 
                FROM costs 
                WHERE costs.section_id = limits.section_id
                  AND strftime('%m', costs.cost_date) = printf('%02d', limits.month)
                  AND strftime('%Y', costs.cost_date) = printf('%d', limits.year)
            ), 0),
            actual_fuel = COALESCE((
                SELECT SUM(fuel) 
                FROM costs 
                WHERE costs.section_id = limits.section_id
                  AND strftime('%m', costs.cost_date) = printf('%02d', limits.month)
                  AND strftime('%Y', costs.cost_date) = printf('%d', limits.year)
            ), 0)
            WHERE 1=1
            """
            
            self.db.execute_query(update_query)
            self.load_data()
            
            QMessageBox.information(self, 'Успех', 'Фактические показатели успешно пересчитаны!')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка пересчета: {str(e)}')