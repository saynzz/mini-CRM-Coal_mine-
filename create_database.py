import sqlite3
from pathlib import Path
from database.db_connection import DatabaseConnection
import sys

def create_tables():
    
    # Удаляем существующий файл базы (для чистой установки)
    db_path = Path('coal_mine.db')
    if db_path.exists():
        db_path.unlink()
    
    db = DatabaseConnection()
    
    # 1. Таблица Должности
    db.execute_query("""
    CREATE TABLE positions (
        position_id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_name TEXT NOT NULL
    )
    """)
    
    # 2. Таблица Уголь
    db.execute_query("""
    CREATE TABLE coal (
        coal_mark TEXT PRIMARY KEY,
        ash_content REAL CHECK (ash_content >= 0 AND ash_content <= 100),
        moisture REAL CHECK (moisture >= 0 AND moisture <= 100),
        calorific_value INTEGER,
        price_per_ton REAL CHECK (price_per_ton > 0)
    )
    """)
    
    # 3. Таблица Участки (без внешнего ключа на работников, чтобы избежать цикла)
    db.execute_query("""
    CREATE TABLE sections (
        section_id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_name TEXT NOT NULL,
        area REAL,
        height REAL,
        manager_tab_number INTEGER
    )
    """)
    
    # 4. Таблица Работники
    db.execute_query("""
    CREATE TABLE workers (
        tab_number INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        section_id INTEGER NOT NULL,
        position_id INTEGER NOT NULL,
        iin TEXT UNIQUE NOT NULL,
        address TEXT,
        phone TEXT,
        gender TEXT CHECK (gender IN ('М', 'Ж')),
        birth_date TEXT,
        FOREIGN KEY (section_id) REFERENCES sections(section_id),
        FOREIGN KEY (position_id) REFERENCES positions(position_id)
    )
    """)
    
    # 5. Таблица Добыча
    db.execute_query("""
    CREATE TABLE mining (
        mining_id INTEGER PRIMARY KEY AUTOINCREMENT,
        mining_date TEXT NOT NULL,
        shift INTEGER CHECK (shift IN (1, 2)),
        volume REAL CHECK (volume >= 0),
        coal_mark TEXT NOT NULL,
        section_id INTEGER NOT NULL,
        rock_volume REAL CHECK (rock_volume >= 0),
        FOREIGN KEY (coal_mark) REFERENCES coal(coal_mark),
        FOREIGN KEY (section_id) REFERENCES sections(section_id)
    )
    """)
    
    # 6. Таблица Затраты
    db.execute_query("""
    CREATE TABLE costs (
        cost_id INTEGER PRIMARY KEY AUTOINCREMENT,
        cost_date TEXT NOT NULL,
        section_id INTEGER NOT NULL,
        shift INTEGER CHECK (shift IN (1, 2)),
        electricity REAL CHECK (electricity >= 0),
        fuel REAL CHECK (fuel >= 0),
        FOREIGN KEY (section_id) REFERENCES sections(section_id)
    )
    """)
    
    # 7. Таблица Учет времени
    db.execute_query("""
    CREATE TABLE time_sheet (
        date TEXT NOT NULL,
        section_id INTEGER NOT NULL,
        shift INTEGER CHECK (shift IN (1, 2)),
        tab_number INTEGER NOT NULL,
        hours REAL CHECK (hours > 0 AND hours <= 12),
        PRIMARY KEY (date, shift, tab_number),
        FOREIGN KEY (tab_number) REFERENCES workers(tab_number),
        FOREIGN KEY (section_id) REFERENCES sections(section_id)
    )
    """)
    
    # 8. Таблица Лимиты
    db.execute_query("""
    CREATE TABLE limits (
        limit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER NOT NULL,
        month INTEGER CHECK (month >= 1 AND month <= 12),
        year INTEGER CHECK (year >= 2000 AND year <= 2100),
        plan_production REAL,
        actual_production REAL DEFAULT 0,
        plan_rock REAL,
        actual_rock REAL DEFAULT 0,
        plan_electricity REAL,
        actual_electricity REAL DEFAULT 0,
        plan_fuel REAL,
        actual_fuel REAL DEFAULT 0,
        UNIQUE(section_id, month, year),
        FOREIGN KEY (section_id) REFERENCES sections(section_id)
    )
    """)
    
    print("Все таблицы успешно созданы!")
    
    # Добавляем тестовые данные
    add_test_data(db)
    
    db.close()
    print("\nБаза данных успешно инициализирована!")
    print(f"   Файл: {db_path.absolute()}")
    print("\nТеперь вы можете запустить приложение: python main.py")

def add_test_data(db):
    
    # 1. Должности
    positions = [
        ('Начальник участка',),
        ('Горный мастер',),
        ('Машинист экскаватора',),
        ('Водитель самосвала',),
        ('Электрослесарь',),
        ('Маркшейдер',)
    ]
    
    db.execute_query("DELETE FROM positions")
    for position in positions:
        db.execute_query("INSERT INTO positions (position_name) VALUES (?)", position)
    
    # 2. Участки
    sections = [
        ('Северный', 1250.5, 45.2, 1001),
        ('Южный', 980.3, 38.7, 1002),
        ('Западный', 1560.8, 52.1, 1003)
    ]
    
    db.execute_query("DELETE FROM sections")
    for section in sections:
        db.execute_query(
            "INSERT INTO sections (section_name, area, height, manager_tab_number) VALUES (?, ?, ?, ?)",
            section
        )
    
    # 3. Работники
    workers = [
        (1001, 'Иванов Иван Иванович', 1, 1, '123456789012', 
         'ул. Ленина, 1', '+7(123)456-78-90', 'М', '1980-05-15'),
        (1002, 'Петров Петр Петрович', 1, 2, '234567890123',
         'ул. Мира, 10', '+7(234)567-89-01', 'М', '1985-08-20'),
        (1003, 'Сидорова Мария Сергеевна', 2, 1, '345678901234',
         'ул. Пушкина, 5', '+7(345)678-90-12', 'Ж', '1990-03-10'),
        (1004, 'Кузнецов Алексей Викторович', 3, 3, '456789012345',
         'ул. Гагарина, 15', '+7(456)789-01-23', 'М', '1988-11-25'),
        (1005, 'Васильев Дмитрий Сергеевич', 2, 4, '567890123456',
         'ул. Садовая, 22', '+7(567)890-12-34', 'М', '1992-07-30')
    ]
    
    db.execute_query("DELETE FROM workers")
    for worker in workers:
        db.execute_query("""
        INSERT INTO workers 
        (tab_number, full_name, section_id, position_id, iin, address, phone, gender, birth_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, worker)
    
    # 4. Уголь
    coal_types = [
        ('Антрацит', 5.5, 3.2, 8100, 8500.00),
        ('Каменный', 8.2, 4.5, 7500, 7200.00),
        ('Бурый', 12.8, 8.7, 5200, 4800.00)
    ]
    
    db.execute_query("DELETE FROM coal")
    for coal in coal_types:
        db.execute_query("""
        INSERT INTO coal (coal_mark, ash_content, moisture, calorific_value, price_per_ton)
        VALUES (?, ?, ?, ?, ?)
        """, coal)
    
    # 5. Лимиты на текущий месяц
    from datetime import datetime
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    limits = [
        (1, current_month, current_year, 50000.0, 12000.0, 25000.0, 8000.0),
        (2, current_month, current_year, 45000.0, 10000.0, 22000.0, 7500.0),
        (3, current_month, current_year, 60000.0, 15000.0, 30000.0, 9000.0)
    ]
    
    db.execute_query("DELETE FROM limits")
    for limit in limits:
        db.execute_query("""
        INSERT INTO limits 
        (section_id, month, year, plan_production, plan_rock, plan_electricity, plan_fuel)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, limit)
    
    print("Тестовые данные успешно добавлены!")

if __name__ == '__main__':
    create_tables()