from flask import Flask, jsonify
import os

# Import modul yang kita buat
from config import Config
from models import db, User 
from auth import bcrypt, hash_password 
from routes import api_bp 



app = Flask(__name__) 
app.config.from_object(Config) 


print(f"DEBUG: SECRET_KEY YANG AKTIF: '{app.config['SECRET_KEY']}'")

db.init_app(app)

bcrypt.init_app(app)


app.register_blueprint(api_bp, url_prefix='/api')



@app.route('/')
def home():
    """Rute dasar untuk memastikan aplikasi berjalan."""
    return jsonify({'message': 'GuardForms Backend API is running smoothly!'}), 200



if __name__ == '__main__':
    
    with app.app_context():
       
        db.create_all()
        print("Status Database: Tabel-tabel database berhasil dibuat atau sudah ada.")

       
        if not db.session.query(db.exists().where(User.username == 'admin')).scalar():
          
            admin_password_hash = hash_password('adminpassword123') 
            admin_user = User(username='admin', email='admin@guardforms.com', password_hash=admin_password_hash, role='admin')
            db.session.add(admin_user) 
            db.session.commit() 
            print("Status Pengguna Admin: Pengguna admin default (username: admin, password: adminpassword123) berhasil dibuat.")
        else:
            print("Status Pengguna Admin: Pengguna admin default sudah ada.")

    
    app.run(debug=True, port=5000)
