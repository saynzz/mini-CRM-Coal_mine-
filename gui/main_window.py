import sys
import webbrowser
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon, QFont
from database.db_connection import DatabaseConnection
from config import Config

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseConnection()
        self.init_ui()
        self.center_window()
        
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def init_ui(self):
        self.setWindowTitle(f'{Config.APP_NAME} v{Config.APP_VERSION}')
        self.setGeometry(100, 100, 1100, 700)
        
        # Создаем меню
        self.create_menu()
        
        # Создаем центральный виджет с вкладками
        self.create_tabs()
        
        # Статус бар
        self.statusBar().showMessage('Готово к работе')
        
        # Применяем стили
        self.apply_styles()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTableView {
                gridline-color: #ddd;
                selection-background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
            }
        """)
    
    def create_menu(self):
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        
        export_action = QAction('Экспорт данных...', self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Выход', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Справочники"
        ref_menu = menubar.addMenu('Справочники')
        
        coal_action = QAction('Уголь', self)
        coal_action.triggered.connect(self.show_coal_management)
        ref_menu.addAction(coal_action)
        
        sections_action = QAction('Участки', self)
        sections_action.triggered.connect(self.show_sections_management)
        ref_menu.addAction(sections_action)
        
        positions_action = QAction('Должности', self)
        positions_action.triggered.connect(self.show_positions_management)
        ref_menu.addAction(positions_action)
        
        workers_action = QAction('Работники', self)
        workers_action.triggered.connect(self.show_workers_management)
        ref_menu.addAction(workers_action)
        
        # Меню "Операции"
        ops_menu = menubar.addMenu('Операции')
        
        mining_action = QAction('Добыча', self)
        mining_action.triggered.connect(self.show_mining_management)
        ops_menu.addAction(mining_action)
        
        costs_action = QAction('Затраты', self)
        costs_action.triggered.connect(self.show_costs_management)
        ops_menu.addAction(costs_action)
        
        time_action = QAction('Учет времени', self)
        time_action.triggered.connect(self.show_timesheet_management)
        ops_menu.addAction(time_action)
        
        # Меню "Планирование"
        plan_menu = menubar.addMenu('Планирование')
        
        limits_action = QAction('Лимиты', self)
        limits_action.triggered.connect(self.show_limits_management)
        plan_menu.addAction(limits_action)
        
        analysis_action = QAction('Анализ выполнения плана', self)
        analysis_action.triggered.connect(self.show_analysis)
        plan_menu.addAction(analysis_action)
        
        # Меню "Отчеты"
        report_menu = menubar.addMenu('Отчеты')
        
        prod_report = QAction('Отчет по добыче', self)
        prod_report.triggered.connect(lambda: self.generate_report('mining'))
        report_menu.addAction(prod_report)
        
        costs_report = QAction('Отчет по затратам', self)
        costs_report.triggered.connect(lambda: self.generate_report('costs'))
        report_menu.addAction(costs_report)
        
        limits_report = QAction('Отчет по лимитам', self)
        limits_report.triggered.connect(lambda: self.generate_report('limits'))
        report_menu.addAction(limits_report)
        
        salary_report = QAction('Расчет заработной платы', self)
        salary_report.triggered.connect(self.generate_salary_report)
        report_menu.addAction(salary_report)
        
        # Меню "Запросы"
        query_menu = menubar.addMenu('Запросы')
        
        custom_query = QAction('Выполнить запрос', self)
        custom_query.triggered.connect(self.show_query_dialog)
        query_menu.addAction(custom_query)
        
        # Меню "Справка"
        help_menu = menubar.addMenu('Справка')
        
        help_action = QAction('Справка', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction('О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tabs(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        # Вкладка "Дашборд"
        dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_tab)
        
        # Заголовок
        title_label = QLabel(f'<h1>{Config.APP_NAME}</h1>')
        title_label.setAlignment(Qt.AlignCenter)
        dashboard_layout.addWidget(title_label)
        
        # Кнопки быстрого доступа
        button_layout = QGridLayout()
        
        buttons = [
            ('Уголь', self.show_coal_management),
            ('Участки', self.show_sections_management),
            ('Работники', self.show_workers_management),
            ('Добыча', self.show_mining_management),
            ('Затраты', self.show_costs_management),
            ('Лимиты', self.show_limits_management),
            ('Отчеты', lambda: self.generate_report('all')),
            ('Запросы', self.show_query_dialog)
        ]
        
        for i, (text, handler) in enumerate(buttons):
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btn.setMinimumHeight(50)
            button_layout.addWidget(btn, i // 4, i % 4)
        
        dashboard_layout.addLayout(button_layout)
        
        # Статистика
        stats_group = QGroupBox('Краткая статистика')
        stats_layout = QGridLayout()
        
        # Получаем статистику из базы
        try:
            # Количество работников
            workers_count = self.db.fetch_one("SELECT COUNT(*) as count FROM workers")['count']
            stats_layout.addWidget(QLabel(f'Работников: {workers_count}'), 0, 0)
            
            # Количество участков
            sections_count = self.db.fetch_one("SELECT COUNT(*) as count FROM sections")['count']
            stats_layout.addWidget(QLabel(f'Участков: {sections_count}'), 0, 1)
            
            # Общая добыча за месяц
            from datetime import datetime
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            mining_total = self.db.fetch_one("""
                SELECT COALESCE(SUM(volume), 0) as total 
                FROM mining 
                WHERE strftime('%m', mining_date) = ? 
                  AND strftime('%Y', mining_date) = ?
            """, (f'{current_month:02d}', str(current_year)))
            
            if mining_total:
                stats_layout.addWidget(QLabel(f'Добыча за месяц: {mining_total["total"]:,.0f} т'), 1, 0)
            
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
        
        stats_group.setLayout(stats_layout)
        dashboard_layout.addWidget(stats_group)
        
        dashboard_layout.addStretch()
        
        self.tab_widget.addTab(dashboard_tab, "Главная")
    
    # Методы для отображения различных форм управления
    def show_coal_management(self):
        from gui.coal_manager import CoalManager
        dialog = CoalManager(self)
        dialog.exec_()
    
    def show_sections_management(self):
        from gui.section_manager import SectionManager
        dialog = SectionManager(self)
        dialog.exec_()
    
    def show_positions_management(self):
        from gui.position_manager import PositionManager
        dialog = PositionManager(self)
        dialog.exec_()
    
    def show_workers_management(self):
        from gui.worker_manager import WorkerManager
        dialog = WorkerManager(self)
        dialog.exec_()
    
    def show_mining_management(self):
        from gui.mining_manager import MiningManager
        dialog = MiningManager(self)
        dialog.exec_()
    
    def show_costs_management(self):
        from gui.cost_manager import CostManager
        dialog = CostManager(self)
        dialog.exec_()
    
    def show_timesheet_management(self):
        from gui.timesheet_manager import TimesheetManager
        dialog = TimesheetManager(self)
        dialog.exec_()
    
    def show_limits_management(self):
        from gui.limit_manager import LimitManager
        dialog = LimitManager(self)
        dialog.exec_()
    
    def show_analysis(self):
        # Запрос для анализа выполнения лимитов
        query = """
        SELECT 
            s.section_name,
            l.month,
            l.year,
            l.plan_production,
            l.actual_production,
            l.plan_rock,
            l.actual_rock,
            CASE 
                WHEN l.plan_production > 0 
                THEN ROUND((l.actual_production * 100.0 / l.plan_production), 2)
                ELSE 0 
            END as production_percent,
            CASE 
                WHEN l.plan_rock > 0 
                THEN ROUND((l.actual_rock * 100.0 / l.plan_rock), 2)
                ELSE 0 
            END as rock_percent
        FROM limits l
        JOIN sections s ON l.section_id = s.section_id
        ORDER BY l.year DESC, l.month DESC, s.section_name
        """
        
        try:
            results = self.db.fetch_all(query)
            
            dialog = QDialog(self)
            dialog.setWindowTitle('Анализ выполнения планов')
            dialog.setMinimumSize(800, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Таблица с результатами
            table = QTableWidget()
            table.setColumnCount(9)
            table.setHorizontalHeaderLabels([
                'Участок', 'Месяц', 'Год', 
                'План добычи', 'Факт добычи', '%',
                'План породы', 'Факт породы', '%'
            ])
            
            table.setRowCount(len(results))
            for i, row in enumerate(results):
                for j, col in enumerate(['section_name', 'month', 'year', 
                                        'plan_production', 'actual_production', 'production_percent',
                                        'plan_rock', 'actual_rock', 'rock_percent']):
                    value = row[col]
                    if j in [3, 4, 6, 7]:  # Числовые значения с форматированием
                        value = f"{float(value):,.0f}" if value else "0"
                    elif j in [5, 8]:  # Проценты
                        value = f"{float(value):.1f}%" if value else "0%"
                    
                    item = QTableWidgetItem(str(value))
                    
                    # Подсветка перевыполнения/недовыполнения
                    if j == 5 and value and float(value.replace('%', '')) < 90:
                        item.setBackground(Qt.yellow)
                    elif j == 5 and value and float(value.replace('%', '')) < 70:
                        item.setBackground(Qt.red)
                    
                    table.setItem(i, j, item)
            
            table.resizeColumnsToContents()
            layout.addWidget(table)
            
            # Кнопки
            btn_box = QDialogButtonBox()
            export_btn = QPushButton('Экспорт в Excel')
            export_btn.clicked.connect(lambda: self.export_to_excel(results, 'analysis'))
            close_btn = QPushButton('Закрыть')
            close_btn.clicked.connect(dialog.close)
            
            btn_box.addButton(export_btn, QDialogButtonBox.ActionRole)
            btn_box.addButton(close_btn, QDialogButtonBox.RejectRole)
            
            layout.addWidget(btn_box)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка выполнения анализа: {str(e)}')
    
    def show_query_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Выполнение SQL запроса')
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Поле для ввода запроса
        query_label = QLabel('Введите SQL запрос:')
        layout.addWidget(query_label)
        
        query_edit = QTextEdit()
        query_edit.setPlaceholderText('SELECT * FROM workers WHERE section_id = 1')
        layout.addWidget(query_edit)
        
        # Кнопки выполнения
        btn_layout = QHBoxLayout()
        
        execute_btn = QPushButton('Выполнить запрос')
        clear_btn = QPushButton('Очистить')
        close_btn = QPushButton('Закрыть')
        
        btn_layout.addWidget(execute_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        # Область для результатов
        result_table = QTableWidget()
        layout.addWidget(result_table)
        
        # Обработчики событий
        def execute_query():
            query = query_edit.toPlainText().strip()
            if not query:
                QMessageBox.warning(dialog, 'Предупреждение', 'Введите SQL запрос')
                return
            
            try:
                # Выполняем запрос
                results = self.db.fetch_all(query)
                
                if not results:
                    QMessageBox.information(dialog, 'Результат', 'Запрос выполнен успешно. Затронуто 0 строк.')
                    result_table.setRowCount(0)
                    result_table.setColumnCount(0)
                    return
                
                # Отображаем результаты в таблице
                result_table.setRowCount(len(results))
                result_table.setColumnCount(len(results[0]))
                
                # Устанавливаем заголовки
                headers = list(results[0].keys())
                result_table.setHorizontalHeaderLabels(headers)
                
                # Заполняем данные
                for i, row in enumerate(results):
                    for j, header in enumerate(headers):
                        value = row[header]
                        item = QTableWidgetItem(str(value) if value is not None else '')
                        result_table.setItem(i, j, item)
                
                result_table.resizeColumnsToContents()
                self.statusBar().showMessage(f'Запрос выполнен. Найдено {len(results)} строк.')
                
            except Exception as e:
                QMessageBox.critical(dialog, 'Ошибка', f'Ошибка выполнения запроса:\n{str(e)}')
        
        def clear_query():
            query_edit.clear()
            result_table.setRowCount(0)
            result_table.setColumnCount(0)
        
        execute_btn.clicked.connect(execute_query)
        clear_btn.clicked.connect(clear_query)
        close_btn.clicked.connect(dialog.close)
        
        dialog.exec_()
    
    def generate_report(self, report_type):
        try:
            if report_type == 'mining':
                query = """
                SELECT 
                    m.mining_date as Дата,
                    s.section_name as Участок,
                    m.coal_mark as Марка_угля,
                    m.volume as Объем_добычи,
                    m.rock_volume as Объем_породы,
                    c.price_per_ton as Цена_за_тонну,
                    (m.volume * c.price_per_ton) as Стоимость_добычи
                FROM mining m
                JOIN sections s ON m.section_id = s.section_id
                JOIN coal c ON m.coal_mark = c.coal_mark
                ORDER BY m.mining_date DESC
                LIMIT 100
                """
                title = 'Отчет по добыче'
                
            elif report_type == 'costs':
                query = """
                SELECT 
                    c.cost_date as Дата,
                    s.section_name as Участок,
                    c.electricity as Электроэнергия_кВтч,
                    c.fuel as Топливо_л,
                    ROUND(c.electricity * 5.5, 2) as Стоимость_электроэнергии,
                    ROUND(c.fuel * 55, 2) as Стоимость_топлива,
                    ROUND(c.electricity * 5.5 + c.fuel * 55, 2) as Общие_затраты
                FROM costs c
                JOIN sections s ON c.section_id = s.section_id
                ORDER BY c.cost_date DESC
                LIMIT 100
                """
                title = 'Отчет по затратам'
                
            elif report_type == 'limits':
                query = """
                SELECT 
                    s.section_name as Участок,
                    l.month as Месяц,
                    l.year as Год,
                    l.plan_production as План_добычи,
                    l.actual_production as Факт_добычи,
                    l.plan_rock as План_породы,
                    l.actual_rock as Факт_породы,
                    CASE 
                        WHEN l.plan_production > 0 
                        THEN ROUND((l.actual_production * 100.0 / l.plan_production), 2)
                        ELSE 0 
                    END as Процент_добычи
                FROM limits l
                JOIN sections s ON l.section_id = s.section_id
                ORDER BY l.year DESC, l.month DESC
                """
                title = 'Отчет по лимитам'
            else:
                return
            
            results = self.db.fetch_all(query)
            
            if not results:
                QMessageBox.information(self, 'Информация', 'Нет данных для отчета.')
                return
            
            # Создаем диалог для отображения отчета
            dialog = QDialog(self)
            dialog.setWindowTitle(title)
            dialog.setMinimumSize(900, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Заголовок отчета
            title_label = QLabel(f'<h2>{title}</h2>')
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # Дата генерации
            from datetime import datetime
            date_label = QLabel(f'Сгенерировано: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
            date_label.setAlignment(Qt.AlignRight)
            layout.addWidget(date_label)
            
            # Таблица с данными
            table = QTableWidget()
            table.setRowCount(len(results))
            
            if results:
                headers = list(results[0].keys())
                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                
                for i, row in enumerate(results):
                    for j, header in enumerate(headers):
                        value = row[header]
                        if isinstance(value, (int, float)) and header not in ['Дата', 'Участок', 'Марка_угля']:
                            # Форматируем числовые значения
                            if value == int(value):
                                display_value = f"{int(value):,}"
                            else:
                                display_value = f"{value:,.2f}"
                        else:
                            display_value = str(value) if value is not None else ''
                        
                        item = QTableWidgetItem(display_value)
                        table.setItem(i, j, item)
                
                table.resizeColumnsToContents()
            
            layout.addWidget(table)
            
            # Кнопки
            btn_layout = QHBoxLayout()
            
            export_excel_btn = QPushButton('Экспорт в Excel')
            export_excel_btn.clicked.connect(lambda: self.export_report_to_excel(results, title))
            
            print_btn = QPushButton('Печать')
            close_btn = QPushButton('Закрыть')
            
            btn_layout.addWidget(export_excel_btn)
            btn_layout.addWidget(print_btn)
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            
            # Обработчики кнопок
            export_excel_btn.clicked.connect(lambda: self.export_report_to_excel(results, title))
            print_btn.clicked.connect(lambda: self.print_report(table, title))
            close_btn.clicked.connect(dialog.close)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка генерации отчета: {str(e)}')
    
    def generate_salary_report(self):
        try:
            # Запрос для расчета зарплаты
            query = """
            SELECT 
                w.tab_number as Табельный_номер,
                w.full_name as ФИО,
                p.position_name as Должность,
                s.section_name as Участок,
                SUM(t.hours) as Отработано_часов,
                SUM(t.hours) * 1500 as Начислено_рублей
            FROM workers w
            JOIN positions p ON w.position_id = p.position_id
            JOIN sections s ON w.section_id = s.section_id
            LEFT JOIN time_sheet t ON w.tab_number = t.tab_number
            WHERE strftime('%m', t.date) = strftime('%m', 'now')
               AND strftime('%Y', t.date) = strftime('%Y', 'now')
            GROUP BY w.tab_number, w.full_name, p.position_name, s.section_name
            ORDER BY s.section_name, w.full_name
            """
            
            results = self.db.fetch_all(query)
            
            if not results:
                QMessageBox.information(self, 'Информация', 'Нет данных для расчета зарплаты.')
                return
            
            dialog = QDialog(self)
            dialog.setWindowTitle('Расчет заработной платы')
            dialog.setMinimumSize(800, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Заголовок
            title_label = QLabel('<h2>Расчет заработной платы</h2>')
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # Период
            from datetime import datetime
            period_label = QLabel(f'Период: {datetime.now().strftime("%B %Y")}')
            period_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(period_label)
            
            # Таблица
            table = QTableWidget()
            table.setRowCount(len(results))
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                'Таб. №', 'ФИО', 'Должность', 'Участок', 
                'Отработано часов', 'Начислено (руб.)'
            ])
            
            total_hours = 0
            total_salary = 0
            
            for i, row in enumerate(results):
                table.setItem(i, 0, QTableWidgetItem(str(row['Табельный_номер'])))
                table.setItem(i, 1, QTableWidgetItem(row['ФИО']))
                table.setItem(i, 2, QTableWidgetItem(row['Должность']))
                table.setItem(i, 3, QTableWidgetItem(row['Участок']))
                table.setItem(i, 4, QTableWidgetItem(f"{row['Отработано_часов'] or 0:.1f}"))
                table.setItem(i, 5, QTableWidgetItem(f"{row['Начислено_рублей'] or 0:,.0f}"))
                
                total_hours += row['Отработано_часов'] or 0
                total_salary += row['Начислено_рублей'] or 0
            
            table.resizeColumnsToContents()
            layout.addWidget(table)
            
            # Итоги
            totals_label = QLabel(
                f'<b>Итого:</b> {len(results)} работников, '
                f'{total_hours:.1f} часов, '
                f'{total_salary:,.0f} рублей'
            )
            totals_label.setAlignment(Qt.AlignRight)
            layout.addWidget(totals_label)
            
            # Кнопки
            btn_box = QDialogButtonBox()
            export_btn = QPushButton('Экспорт в Excel')
            close_btn = QPushButton('Закрыть')
            
            btn_box.addButton(export_btn, QDialogButtonBox.ActionRole)
            btn_box.addButton(close_btn, QDialogButtonBox.RejectRole)
            
            layout.addWidget(btn_box)
            
            # Обработчики
            export_btn.clicked.connect(lambda: self.export_to_excel(results, 'salary'))
            close_btn.clicked.connect(dialog.close)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка расчета зарплаты: {str(e)}')
    
    def export_data(self):
        try:
            import pandas as pd
            from datetime import datetime
            
            # Получаем все таблицы
            tables = ['positions', 'coal', 'sections', 'workers', 
                     'mining', 'costs', 'time_sheet', 'limits']
            
            # Создаем Excel writer
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/export_all_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for table in tables:
                    query = f"SELECT * FROM {table}"
                    data = self.db.fetch_all(query)
                    
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=table, index=False)
            
            QMessageBox.information(
                self, 'Экспорт завершен',
                f'Все данные успешно экспортированы в файл:\n{filename}'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка экспорта: {str(e)}')
    
    def export_to_excel(self, data, report_name):
        try:
            import pandas as pd
            from datetime import datetime
            
            if not data:
                QMessageBox.warning(self, 'Предупреждение', 'Нет данных для экспорта')
                return
            
            df = pd.DataFrame(data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/{report_name}_{timestamp}.xlsx"
            
            df.to_excel(filename, index=False)
            
            QMessageBox.information(
                self, 'Успешный экспорт',
                f'Данные успешно экспортированы в файл:\n{filename}'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка экспорта: {str(e)}')
    
    def export_report_to_excel(self, data, title):
        try:
            import pandas as pd
            from datetime import datetime
            
            if not data:
                return
            
            df = pd.DataFrame(data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/{title}_{timestamp}.xlsx".replace(' ', '_')
            
            # Создаем Excel writer для форматирования
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Отчет', index=False)
                
                # Получаем workbook и worksheet для форматирования
                workbook = writer.book
                worksheet = writer.sheets['Отчет']
                
                # Настраиваем ширину колонок
                for column in df:
                    column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                    col_idx = df.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width, 50)
            
            QMessageBox.information(
                self, 'Экспорт завершен',
                f'Отчет успешно экспортирован в файл:\n{filename}'
            )
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка экспорта: {str(e)}')
    
    def print_report(self, table, title):
        QMessageBox.information(
            self, 'Печать',
            'Функция печати будет реализована в следующей версии.\n'
            'Пока используйте экспорт в Excel для печати.'
        )
    
    def show_help(self):
        help_file = Config.HELP_FILE
        if help_file.exists():
            webbrowser.open(f'file://{help_file.absolute()}')
        else:
            # Встроенная справка
            help_dialog = QDialog(self)
            help_dialog.setWindowTitle('Справка')
            help_dialog.setMinimumSize(500, 400)
            
            layout = QVBoxLayout(help_dialog)
            
            help_text = QTextEdit()
            help_text.setReadOnly(True)
            help_text.setHtml("""
            <h2>Справка по системе "Угольная Шахта"</h2>
            <h3>Основные возможности:</h3>
            <ul>
                <li><b>Управление справочниками:</b> уголь, участки, должности, работники</li>
                <li><b>Учет операций:</b> добыча угля, затраты ресурсов, учет рабочего времени</li>
                <li><b>Планирование:</b> установка лимитов и контроль их выполнения</li>
                <li><b>Отчетность:</b> автоматическое формирование отчетов</li>
                <li><b>Аналитика:</b> анализ эффективности работы участков</li>
            </ul>
            <h3>Рекомендуемый порядок работы:</h3>
            <ol>
                <li>Заполните справочники (Должности → Участки → Работники → Уголь)</li>
                <li>Вносите ежедневные данные по добыче и затратам</li>
                <li>Установите месячные лимиты для участков</li>
                <li>Анализируйте выполнение планов через соответствующие отчеты</li>
            </ol>
            <h3>Техническая информация:</h3>
            <p>Система использует базу данных SQLite, которая хранится в файле <code>coal_mine.db</code></p>
            <p>Все данные можно экспортировать в Excel для дальнейшей обработки</p>
            """)
            
            layout.addWidget(help_text)
            
            close_btn = QPushButton('Закрыть')
            close_btn.clicked.connect(help_dialog.close)
            layout.addWidget(close_btn)
            
            help_dialog.exec_()
    
    def show_about(self):
        QMessageBox.about(
            self, 'О программе',
            f'<h3>{Config.APP_NAME}</h3>'
            f'<p>Версия: {Config.APP_VERSION}</p>'
            '<p>Система управления угольной шахтой</p>'
            '<p>Функции:</p>'
            '<ul>'
            '<li>Управление справочной информацией</li>'
            '<li>Учет производственных операций</li>'
            '<li>Планирование и контроль выполнения</li>'
            '<li>Формирование отчетности</li>'
            '</ul>'
            '<p>Разработано для лабораторной работы по базам данных</p>'
        )
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Подтверждение выхода',
            'Вы уверены, что хотите выйти из программы?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.close()
            event.accept()
        else:
            event.ignore()