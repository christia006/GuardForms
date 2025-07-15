import os

class Config:
 
    SECRET_KEY = 'MY_SIMPLE_TEST_KEY' 

    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

  
    DB_CONFIG_POSTGRES = {
        "dbname": "neurosordb",
        "user": "neurosord_user",
        "password": "Sayabag",
        "host": "localhost",
        "port": "5432"
    }
