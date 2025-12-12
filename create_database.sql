-- Для SQLite (create_database_sqlite.sql)
-- 1. Таблица Должности
CREATE TABLE IF NOT EXISTS positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_name TEXT NOT NULL
);

-- 2. Таблица Уголь
CREATE TABLE IF NOT EXISTS coal (
    coal_mark TEXT PRIMARY KEY,
    ash_content REAL CHECK (ash_content >= 0 AND ash_content <= 100),
    moisture REAL CHECK (moisture >= 0 AND moisture <= 100),
    calorific_value INTEGER,
    price_per_ton REAL CHECK (price_per_ton > 0)
);

-- 3. Таблица Участки
CREATE TABLE IF NOT EXISTS sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_name TEXT NOT NULL,
    area REAL,
    height REAL,
    manager_tab_number INTEGER UNIQUE
);

-- 4. Таблица Работники
CREATE TABLE IF NOT EXISTS workers (
    tab_number INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    section_id INTEGER NOT NULL,
    position_id INTEGER NOT NULL,
    iin TEXT UNIQUE NOT NULL,
    address TEXT,
    phone TEXT,
    gender TEXT CHECK (gender IN ('М', 'Ж')),
    birth_date TEXT, 
    FOREIGN KEY (section_id) REFERENCES sections(section_id) ON DELETE CASCADE,
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

PRAGMA foreign_keys=OFF;
DROP TABLE IF EXISTS sections;
CREATE TABLE sections (
    section_id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_name TEXT NOT NULL,
    area REAL,
    height REAL,
    manager_tab_number INTEGER UNIQUE,
    FOREIGN KEY (manager_tab_number) REFERENCES workers(tab_number) ON DELETE SET NULL
);
PRAGMA foreign_keys=ON;