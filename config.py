import os

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-yang-sangat-rahasia-dan-panjang-untuk-pengembangan'

 
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Mengatur ini ke False menghemat memori.

    DB_CONFIG_POSTGRES = {
        "dbname": "neurosordb",
        "user": "neurosord_user",
        "password": "Sayabag",
        "host": "localhost",
        "port": "5432"
    }