import sqlite3
from datetime import datetime
from pathlib import Path

# Создаем или подключаем базу данных
DB_FILE = "smartphone_defects.db"
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Таблица производителей
cursor.execute('''
CREATE TABLE IF NOT EXISTS manufacturer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    country TEXT
)
''')

# Таблица моделей смартфонов
cursor.execute('''
CREATE TABLE IF NOT EXISTS smartphone_model (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manufacturer_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    release_year INTEGER,
    screen_type TEXT CHECK(screen_type IN ('OLED', 'LCD', 'AMOLED', 'IPS')),
    screen_size REAL,
    FOREIGN KEY (manufacturer_id) REFERENCES manufacturer(id),
    UNIQUE(manufacturer_id, model_name)
)
''')

# Таблица типов дефектов
cursor.execute('''
CREATE TABLE IF NOT EXISTS defect_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
)
''')

# Таблица локаций дефектов
cursor.execute('''
CREATE TABLE IF NOT EXISTS defect_location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
)
''')

# Таблица уровней серьезности
cursor.execute('''
CREATE TABLE IF NOT EXISTS severity_level (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level_name TEXT NOT NULL UNIQUE,
    score INTEGER NOT NULL UNIQUE
)
''')

# Таблица устройств
cursor.execute('''
CREATE TABLE IF NOT EXISTS device (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    imei TEXT UNIQUE,
    production_date DATE,
    FOREIGN KEY (model_id) REFERENCES smartphone_model(id)
)
''')

# Таблица дефектов
cursor.execute('''
CREATE TABLE IF NOT EXISTS defect (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    defect_type_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    severity_id INTEGER NOT NULL,
    detection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    length_mm REAL,
    width_mm REAL,
    description TEXT,
    is_repaired BOOLEAN DEFAULT FALSE,
    repair_date DATETIME,
    FOREIGN KEY (device_id) REFERENCES device(id),
    FOREIGN KEY (defect_type_id) REFERENCES defect_type(id),
    FOREIGN KEY (location_id) REFERENCES defect_location(id),
    FOREIGN KEY (severity_id) REFERENCES severity_level(id)
)
''')

# Таблица изображений дефектов
cursor.execute('''
CREATE TABLE IF NOT EXISTS defect_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    defect_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    capture_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_date DATETIME,
    FOREIGN KEY (defect_id) REFERENCES defect(id)
)
''')

# Таблица техников
cursor.execute('''
CREATE TABLE IF NOT EXISTS technician (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    specialization TEXT,
    hire_date DATE
)
''')

# Таблица диагностики
cursor.execute('''
CREATE TABLE IF NOT EXISTS diagnosis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    defect_id INTEGER NOT NULL,
    technician_id INTEGER NOT NULL,
    diagnosis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    conclusion TEXT,
    recommended_action TEXT,
    FOREIGN KEY (defect_id) REFERENCES defect(id),
    FOREIGN KEY (technician_id) REFERENCES technician(id)
)
''')

# Таблица ремонтов
cursor.execute('''
CREATE TABLE IF NOT EXISTS repair (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    defect_id INTEGER NOT NULL,
    technician_id INTEGER NOT NULL,
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_date DATETIME,
    repair_type TEXT,
    cost REAL,
    status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
    warranty_until DATE,
    FOREIGN KEY (defect_id) REFERENCES defect(id),
    FOREIGN KEY (technician_id) REFERENCES technician(id)
)
''')

# Заполнение начальными данными
# Производители
manufacturers = [
    ('Apple', 'USA'),
    ('Samsung', 'South Korea'),
    ('Xiaomi', 'China'),
    ('Huawei', 'China'),
    ('OnePlus', 'China')
]
cursor.executemany('INSERT INTO manufacturer (name, country) VALUES (?, ?)', manufacturers)

# Типы дефектов
defect_types = [
    ('Царапина', 'Поверхностное повреждение защитного стекла'),
    ('Скол', 'Локальное повреждение края экрана'),
    ('Трещина', 'Линейное повреждение экрана'),
    ('Паутина', 'Множественные радиальные трещины'),
    ('Пятно', 'Повреждение дисплея под стеклом')
]
cursor.executemany('INSERT INTO defect_type (name, description) VALUES (?, ?)', defect_types)

# Локации дефектов
locations = [
    ('Верхний край', 'Верхняя часть экрана'),
    ('Нижний край', 'Нижняя часть экрана'),
    ('Левый край', 'Левая часть экрана'),
    ('Правый край', 'Правая часть экрана'),
    ('Центр', 'Центральная часть экрана'),
    ('Угол', 'Один из углов экрана')
]
cursor.executemany('INSERT INTO defect_location (name, description) VALUES (?, ?)', locations)

# Уровни серьезности
severity_levels = [
    ('Минимальный', 1),
    ('Незначительный', 2),
    ('Умеренный', 3),
    ('Серьезный', 4),
    ('Критический', 5)
]
cursor.executemany('INSERT INTO severity_level (level_name, score) VALUES (?, ?)', severity_levels)

# Модели смартфонов
smartphone_models = [
    (1, 'iPhone 13', 2021, 'OLED', 6.1),
    (1, 'iPhone SE', 2022, 'LCD', 4.7),
    (2, 'Galaxy S22', 2022, 'AMOLED', 6.1),
    (2, 'Galaxy A53', 2022, 'AMOLED', 6.5),
    (3, 'Redmi Note 11', 2022, 'AMOLED', 6.43),
    (4, 'P50 Pro', 2021, 'OLED', 6.6),
    (5, '10 Pro', 2022, 'AMOLED', 6.7)
]
cursor.executemany('''
INSERT INTO smartphone_model 
(manufacturer_id, model_name, release_year, screen_type, screen_size) 
VALUES (?, ?, ?, ?, ?)
''', smartphone_models)

# Техники
technicians = [
    ('Иванов Алексей', 'ivanov@service.com', '+79161234567', 'Экраны', '2020-05-15'),
    ('Петрова Мария', 'petrova@service.com', '+79167654321', 'Корпуса', '2021-02-10'),
    ('Сидоров Дмитрий', 'sidorov@service.com', '+79169998877', 'Диагностика', '2019-11-23')
]
cursor.executemany('''
INSERT INTO technician 
(name, email, phone, specialization, hire_date) 
VALUES (?, ?, ?, ?, ?)
''', technicians)

# Устройства
devices = [
    (1, '354678901234567', '2021-09-01'),
    (3, '456789012345678', '2022-03-15'),
    (5, '567890123456789', '2022-05-20'),
    (7, '678901234567890', '2022-07-10')
]
cursor.executemany('''
INSERT INTO device 
(model_id, imei, production_date) 
VALUES (?, ?, ?)
''', devices)

# Дефекты
defects = [
    (1, 1, 5, 2, '2022-10-15 09:30:00', 15.2, 0.1, 'Длинная тонкая царапина'),
    (1, 2, 6, 3, '2022-10-15 09:30:00', 2.5, 2.5, 'Скол в левом нижнем углу'),
    (2, 3, 1, 4, '2022-11-02 14:15:00', 35.0, 0.5, 'Трещина от верха до центра'),
    (3, 1, 3, 1, '2022-11-10 11:20:00', 8.7, 0.05, 'Несколько мелких царапин'),
    (4, 4, 2, 5, '2022-11-25 16:45:00', None, None, 'Паутина по всему экрану')
]
cursor.executemany('''
INSERT INTO defect 
(device_id, defect_type_id, location_id, severity_id, detection_date, 
 length_mm, width_mm, description) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', defects)

# Изображения дефектов
images = [
    (1, 'images/defect_1_1.jpg', '2022-10-15 09:32:00', True, '2022-10-15 10:15:00'),
    (1, 'images/defect_1_2.jpg', '2022-10-15 09:33:00', True, '2022-10-15 10:15:00'),
    (2, 'images/defect_2_1.jpg', '2022-11-02 14:20:00', True, '2022-11-02 15:30:00'),
    (3, 'images/defect_3_1.jpg', '2022-11-10 11:25:00', False, None),
    (4, 'images/defect_4_1.jpg', '2022-11-25 16:50:00', True, '2022-11-25 17:30:00')
]
cursor.executemany('''
INSERT INTO defect_image 
(defect_id, image_path, capture_date, is_verified, verification_date) 
VALUES (?, ?, ?, ?, ?)
''', images)

# Диагностики
diagnoses = [
    (1, 1, '2022-10-15 10:00:00', 'Поверхностная царапина, не влияет на функциональность', 'Полировка экрана'),
    (2, 1, '2022-10-15 10:05:00', 'Скол края экрана, возможны дальнейшие повреждения', 'Замена защитного стекла'),
    (3, 2, '2022-11-02 15:00:00', 'Сквозная трещина, требуется замена экрана', 'Полная замена дисплея'),
    (5, 3, '2022-11-25 17:00:00', 'Множественные трещины, дисплей не функционирует', 'Замена дисплейного модуля')
]
cursor.executemany('''
INSERT INTO diagnosis 
(defect_id, technician_id, diagnosis_date, conclusion, recommended_action) 
VALUES (?, ?, ?, ?, ?)
''', diagnoses)

# Ремонты
repairs = [
    (1, 1, '2022-10-15 10:30:00', '2022-10-15 11:15:00', 'Полировка', 1500.0, 'completed', '2023-10-15'),
    (3, 2, '2022-11-03 10:00:00', '2022-11-03 12:30:00', 'Замена дисплея', 12000.0, 'completed', '2023-11-03'),
    (5, 1, '2022-11-26 10:00:00', None, 'Замена дисплейного модуля', 8500.0, 'in_progress', None)
]
cursor.executemany('''
INSERT INTO repair 
(defect_id, technician_id, start_date, end_date, repair_type, cost, status, warranty_until) 
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', repairs)

# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()

print(f"База данных {DB_FILE} успешно создана и заполнена тестовыми данными.")
