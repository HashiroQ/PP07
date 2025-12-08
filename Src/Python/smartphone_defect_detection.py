import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
import os
from datetime import datetime
import json
from PIL import Image, ImageTk
import threading

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.db_path = None
        
    def connect(self, db_path):
        """Подключение к базе данных"""
        try:
            self.connection = sqlite3.connect(db_path)
            self.db_path = db_path
            self.create_tables()
            self.create_default_admin()
            return True
        except Exception as e:
            messagebox.showerror("Ошибка подключения", str(e))
            return False
    
    def create_tables(self):
        """Создание таблиц, если они не существуют"""
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'inspector', 'viewer')),
                full_name TEXT,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS smartphones (
                smartphone_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                screen_size REAL,
                resolution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS inspections (
                inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                smartphone_id INTEGER,
                inspector_id INTEGER,
                inspection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'rejected')),
                overall_result TEXT CHECK(overall_result IN ('pass', 'fail', 'conditional')),
                notes TEXT,
                image_path TEXT,
                FOREIGN KEY (smartphone_id) REFERENCES smartphones(smartphone_id),
                FOREIGN KEY (inspector_id) REFERENCES users(user_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS defects (
                defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_id INTEGER,
                defect_type TEXT CHECK(defect_type IN ('scratch', 'chip', 'crack', 'discoloration', 'other')),
                severity INTEGER CHECK(severity BETWEEN 1 AND 5),
                location_x INTEGER,
                location_y INTEGER,
                size REAL,
                description TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inspection_id) REFERENCES inspections(inspection_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS defect_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_id INTEGER,
                image_path TEXT NOT NULL,
                thumbnail_path TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (defect_id) REFERENCES defects(defect_id)
            )"""
        ]
        
        cursor = self.connection.cursor()
        for table in tables:
            cursor.execute(table)
        self.connection.commit()
    
    def create_default_admin(self):
        """Создание администратора по умолчанию"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        if cursor.fetchone()[0] == 0:
            admin_password = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                ("admin", admin_password, "admin", "Администратор")
            )
            self.connection.commit()
    
    def hash_password(self, password):
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """Аутентификация пользователя"""
        cursor = self.connection.cursor()
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT user_id, username, role, full_name FROM users WHERE username=? AND password_hash=?",
            (username, password_hash)
        )
        return cursor.fetchone()
    
    def execute_query(self, query, params=()):
        """Выполнение запроса"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor
    
    def fetch_all(self, query, params=()):
        """Получение всех результатов запроса"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        """Получение одного результата запроса"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

class LoginWindow:
    def __init__(self, root, db_manager, on_login_success):
        self.root = root
        self.db_manager = db_manager
        self.on_login_success = on_login_success
        
        self.window = tk.Toplevel(root)
        self.window.title("Вход в систему")
        self.window.geometry("300x200")
        self.window.resizable(False, False)
        
        self.center_window(self.window)
        
        self.create_widgets()
    
    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        tk.Label(self.window, text="Система контроля качества", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        frame = tk.Frame(self.window)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Имя пользователя:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(frame, width=20)
        self.username_entry.grid(row=0, column=1, pady=5)
        
        tk.Label(frame, text="Пароль:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = tk.Entry(frame, width=20, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)
        
        tk.Button(self.window, text="Войти", command=self.login, 
                 bg="#4CAF50", fg="white", width=15).pack(pady=20)
        
        self.username_entry.insert(0, "admin")
        self.password_entry.insert(0, "admin123")
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return
        
        user = self.db_manager.authenticate(username, password)
        if user:
            self.window.destroy()
            self.on_login_success(user)
        else:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Система обнаружения дефектов экранов смартфонов")
        self.root.geometry("1200x700")
        
        self.db_manager = DatabaseManager()
        self.current_user = None
        
        self.create_menu()
        
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)
        
        self.show_connection_screen()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Подключить БД", command=self.show_connection_screen)
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        self.tables_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Таблицы", menu=self.tables_menu)
        
        self.admin_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Администрирование", menu=self.admin_menu)
    
    def show_connection_screen(self):
        """Отображение экрана подключения к БД"""
        self.clear_main_frame()
        
        tk.Label(self.main_frame, text="Подключение к базе данных", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        frame = tk.Frame(self.main_frame)
        frame.pack(pady=20)
        
        tk.Label(frame, text="Путь к базе данных:").grid(row=0, column=0, sticky="w", pady=10)
        self.db_path_entry = tk.Entry(frame, width=50)
        self.db_path_entry.grid(row=0, column=1, pady=10, padx=5)
        
        tk.Button(frame, text="Обзор", command=self.browse_db_file).grid(row=0, column=2, padx=5)
        
        tk.Button(frame, text="Создать новую БД", command=self.create_new_db).grid(row=1, column=0, pady=20)
        tk.Button(frame, text="Подключиться", command=self.connect_db, 
                 bg="#4CAF50", fg="white").grid(row=1, column=1, pady=20)
        
        tk.Button(frame, text="Тестовое подключение", command=self.test_connection).grid(row=1, column=2, pady=20)
    
    def browse_db_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[("SQLite databases", "*.db *.sqlite"), ("All files", "*.*")]
        )
        if filename:
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, filename)
    
    def create_new_db(self):
        filename = filedialog.asksaveasfilename(
            title="Создать новую базу данных",
            defaultextension=".db",
            filetypes=[("SQLite databases", "*.db"), ("All files", "*.*")]
        )
        if filename:
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, filename)
            self.connect_db()
    
    def test_connection(self):
        """Тестовое подключение к базе данных"""
        self.db_path_entry.delete(0, tk.END)
        self.db_path_entry.insert(0, "smartphone_defects.db")
        self.connect_db()
    
    def connect_db(self):
        db_path = self.db_path_entry.get()
        if not db_path:
            messagebox.showwarning("Ошибка", "Укажите путь к базе данных")
            return
        
        if self.db_manager.connect(db_path):
            messagebox.showinfo("Успех", "База данных успешно подключена")
            self.show_login_window()
    
    def show_login_window(self):
        LoginWindow(self.root, self.db_manager, self.on_login_success)
    
    def on_login_success(self, user):
        """Обработка успешного входа"""
        self.current_user = {
            'id': user[0],
            'username': user[1],
            'role': user[2],
            'full_name': user[3]
        }
        
        self.update_menu()
        
        self.show_main_panel()
    
    def update_menu(self):
        """Обновление меню в зависимости от роли пользователя"""
        self.tables_menu.delete(0, tk.END)
        self.admin_menu.delete(0, tk.END)
        
        self.tables_menu.add_command(label="Смартфоны", command=lambda: self.show_table("smartphones"))
        self.tables_menu.add_command(label="Инспекции", command=lambda: self.show_table("inspections"))
        self.tables_menu.add_command(label="Дефекты", command=lambda: self.show_table("defects"))
        self.tables_menu.add_command(label="Изображения дефектов", command=lambda: self.show_table("defect_images"))
        
        if self.current_user['role'] == 'admin':
            self.admin_menu.add_command(label="Пользователи", command=lambda: self.show_table("users"))
            self.admin_menu.add_command(label="Статистика", command=self.show_statistics)
    
    def show_main_panel(self):
        """Отображение главной панели"""
        self.clear_main_frame()
        
        tk.Label(self.main_frame, text=f"Добро пожаловать, {self.current_user['full_name']}!", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        stats_frame = tk.LabelFrame(self.main_frame, text="Статистика", padx=20, pady=20)
        stats_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        stats = self.get_statistics()
        
        row = 0
        for key, value in stats.items():
            tk.Label(stats_frame, text=f"{key}: {value}", font=("Arial", 12)).grid(
                row=row, column=0, sticky="w", pady=5)
            row += 1
    
    def get_statistics(self):
        """Получение статистики из базы данных"""
        stats = {}
        
        try:
            result = self.db_manager.fetch_one("SELECT COUNT(*) FROM smartphones")
            stats["Всего смартфонов"] = result[0]
            
            result = self.db_manager.fetch_one("SELECT COUNT(*) FROM inspections")
            stats["Всего проверок"] = result[0]
            
            result = self.db_manager.fetch_one("SELECT COUNT(*) FROM defects")
            stats["Найдено дефектов"] = result[0]
            
            result = self.db_manager.fetch_one(
                "SELECT COUNT(*) FROM inspections WHERE DATE(inspection_date) = DATE('now')"
            )
            stats["Проверок сегодня"] = result[0]
            
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
        
        return stats
    
    def show_table(self, table_name):
        """Отображение таблицы с данными"""
        self.clear_main_frame()
        
        tk.Label(self.main_frame, text=f"Таблица: {table_name}", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        toolbar = tk.Frame(self.main_frame)
        toolbar.pack(fill="x", padx=10, pady=5)
        
        tk.Button(toolbar, text="Добавить", command=lambda: self.add_record(table_name),
                 bg="#4CAF50", fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="Редактировать", command=lambda: self.edit_record(table_name),
                 bg="#2196F3", fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="Удалить", command=lambda: self.delete_record(table_name),
                 bg="#f44336", fg="white").pack(side="left", padx=5)
        tk.Button(toolbar, text="Обновить", command=lambda: self.refresh_table(table_name)).pack(side="left", padx=5)
        
        table_frame = tk.Frame(self.main_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(table_frame)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.load_table_data(table_name)
    
    def load_table_data(self, table_name):
        """Загрузка данных таблицы в Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            self.tree["columns"] = [col[1] for col in columns]
            self.tree["show"] = "headings"
            
            for col in columns:
                self.tree.heading(col[1], text=col[1])
                self.tree.column(col[1], width=100)
            
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            for row in rows:
                self.tree.insert("", "end", values=row)
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {str(e)}")
    
    def add_record(self, table_name):
        """Добавление новой записи"""
        dialog = RecordDialog(self.root, self.db_manager, table_name, "add", None)
        if dialog.result:
            self.refresh_table(table_name)
    
    def edit_record(self, table_name):
        """Редактирование записи"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите запись для редактирования")
            return
        
        item = self.tree.item(selected_item[0])
        record_id = item['values'][0]  
        
        dialog = RecordDialog(self.root, self.db_manager, table_name, "edit", record_id)
        if dialog.result:
            self.refresh_table(table_name)
    
    def delete_record(self, table_name):
        """Удаление записи"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить выбранную запись?"):
            item = self.tree.item(selected_item[0])
            record_id = item['values'][0]
            
            try:
                cursor = self.db_manager.connection.cursor()
                cursor.execute(f"DELETE FROM {table_name} WHERE rowid=?", (record_id,))
                self.db_manager.connection.commit()
                messagebox.showinfo("Успех", "Запись успешно удалена")
                self.refresh_table(table_name)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def refresh_table(self, table_name):
        """Обновление таблицы"""
        self.load_table_data(table_name)
    
    def show_statistics(self):
        """Отображение статистики"""
        self.clear_main_frame()
        
        tk.Label(self.main_frame, text="Статистика системы", 
                font=("Arial", 16, "bold")).pack(pady=20)
        
        
        stats_frame = tk.Frame(self.main_frame)
        stats_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        stats = self.get_detailed_statistics()
        
        row = 0
        for category, data in stats.items():
            tk.Label(stats_frame, text=category, font=("Arial", 12, "bold")).grid(
                row=row, column=0, sticky="w", pady=10)
            row += 1
            
            for key, value in data.items():
                tk.Label(stats_frame, text=f"  {key}: {value}").grid(
                    row=row, column=0, sticky="w", padx=20)
                row += 1
    
    def get_detailed_statistics(self):
        """Получение детальной статистики"""
        stats = {}
        
        try:
            defect_stats = {}
            result = self.db_manager.fetch_all(
                "SELECT defect_type, COUNT(*) FROM defects GROUP BY defect_type"
            )
            for row in result:
                defect_stats[row[0]] = row[1]
            stats["Статистика по типам дефектов"] = defect_stats
            
            manufacturer_stats = {}
            result = self.db_manager.fetch_all(
                "SELECT manufacturer, COUNT(*) FROM smartphones GROUP BY manufacturer"
            )
            for row in result:
                manufacturer_stats[row[0]] = row[1]
            stats["Статистика по производителям"] = manufacturer_stats
            
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
        
        return stats
    
    def clear_main_frame(self):
        """Очистка основного фрейма"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

class RecordDialog:
    def __init__(self, parent, db_manager, table_name, mode, record_id=None):
        self.parent = parent
        self.db_manager = db_manager
        self.table_name = table_name
        self.mode = mode
        self.record_id = record_id
        self.result = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{'Добавить' if mode == 'add' else 'Редактировать'} запись")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.center_window(self.dialog)
        self.create_widgets()
        self.load_data()
        
        self.dialog.wait_window()
    
    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        self.entries = {}
        self.labels_frame = tk.Frame(main_frame)
        self.labels_frame.pack(fill="both", expand=True)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=20)
        
        tk.Button(button_frame, text="Сохранить", command=self.save,
                 bg="#4CAF50", fg="white", width=15).pack(side="left", padx=5)
        tk.Button(button_frame, text="Отмена", command=self.dialog.destroy,
                 bg="#f44336", fg="white", width=15).pack(side="right", padx=5)
    
    def load_data(self):
        """Загрузка структуры таблицы и данных записи"""
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            
            skip_columns = ['created_at', 'uploaded_at', 'detected_at', 'inspection_date']
            
            row = 0
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                
                if col_name in skip_columns or (col[5] == 1 and self.mode == 'add'):
                    continue
                
                tk.Label(self.labels_frame, text=col_name).grid(
                    row=row, column=0, sticky="w", pady=5)
                
                if 'password' in col_name.lower():
                    entry = tk.Entry(self.labels_frame, width=30, show="*")
                else:
                    entry = tk.Entry(self.labels_frame, width=30)
                
                entry.grid(row=row, column=1, pady=5, padx=10)
                self.entries[col_name] = entry
                
                if col_name == 'role':
                    entry.destroy()
                    combo = ttk.Combobox(self.labels_frame, values=['admin', 'inspector', 'viewer'], width=28)
                    combo.grid(row=row, column=1, pady=5, padx=10)
                    self.entries[col_name] = combo
                elif col_name == 'defect_type':
                    entry.destroy()
                    combo = ttk.Combobox(self.labels_frame, 
                                        values=['scratch', 'chip', 'crack', 'discoloration', 'other'], 
                                        width=28)
                    combo.grid(row=row, column=1, pady=5, padx=10)
                    self.entries[col_name] = combo
                elif col_name in ['status', 'overall_result', 'severity']:
                    entry.destroy()
                    if col_name == 'severity':
                        values = [1, 2, 3, 4, 5]
                    elif col_name == 'status':
                        values = ['pending', 'in_progress', 'completed', 'rejected']
                    elif col_name == 'overall_result':
                        values = ['pass', 'fail', 'conditional']
                    combo = ttk.Combobox(self.labels_frame, values=values, width=28)
                    combo.grid(row=row, column=1, pady=5, padx=10)
                    self.entries[col_name] = combo
                
                row += 1
            
            if self.mode == 'edit' and self.record_id:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE rowid=?", (self.record_id,))
                record = cursor.fetchone()
                
                if record:
                    for i, col in enumerate(columns):
                        col_name = col[1]
                        if col_name in self.entries:
                            widget = self.entries[col_name]
                            if isinstance(widget, ttk.Combobox):
                                widget.set(record[i])
                            else:
                                widget.insert(0, str(record[i]) if record[i] else "")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных: {str(e)}")
            self.dialog.destroy()
    
    def save(self):
        """Сохранение записи"""
        try:
            data = {}
            for col_name, widget in self.entries.items():
                if isinstance(widget, ttk.Combobox):
                    value = widget.get()
                else:
                    value = widget.get()
                
                if 'password' in col_name.lower() and value:
                    value = self.db_manager.hash_password(value)
                
                data[col_name] = value
            
            cursor = self.db_manager.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            
            for col in columns:
                if col[3] == 1 and col[1] in data and not data[col[1]]:
                    messagebox.showwarning("Ошибка", f"Поле '{col[1]}' обязательно для заполнения")
                    return
            
            if self.mode == 'add':
                columns_str = ', '.join(data.keys())
                placeholders = ', '.join(['?' for _ in data])
                query = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                params = tuple(data.values())
            else:
                set_clause = ', '.join([f"{col}=?" for col in data.keys()])
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE rowid=?"
                params = tuple(data.values()) + (self.record_id,)
            
            self.db_manager.execute_query(query, params)
            messagebox.showinfo("Успех", "Данные успешно сохранены")
            self.result = True
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении: {str(e)}")

def main():
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()

if __name__ == "__main__":
    main()