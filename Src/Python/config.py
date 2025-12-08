import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'databases')
    IMAGES_DIR = os.path.join(BASE_DIR, 'images')
    
    for directory in [DATABASE_DIR, IMAGES_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    DEFAULT_DB = os.path.join(DATABASE_DIR, 'smartphone_defects.db')
    
    APP_NAME = "Система обнаружения дефектов экранов смартфонов"
    APP_VERSION = "1.0.0"
    
    PRIMARY_COLOR = "#2196F3"
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#FF9800"
    ERROR_COLOR = "#f44336"
    
    @staticmethod
    def get_db_path(db_name):
        return os.path.join(Config.DATABASE_DIR, db_name)