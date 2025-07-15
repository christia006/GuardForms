from flask import Flask, jsonify
from dotenv import load_dotenv # Untuk memuat variabel lingkungan dari .env
import os

# Import modul yang kita buat
from config import Config
from models import db, User # Import db dan User dari models.py
from auth import bcrypt, hash_password # Import bcrypt dan hash_password dari auth.py
from routes import api_bp # Import Blueprint API

# --- Inisialisasi Aplikasi Flask ---

# Memuat variabel lingkungan dari file .env
load_dotenv()

app = Flask(__name__) # Membuat instance aplikasi Flask
app.config.from_object(Config) # Memuat konfigurasi dari objek Config

# --- Inisialisasi Ekstensi Flask ---

# Mengaitkan objek SQLAlchemy (db) dengan aplikasi Flask
db.init_app(app)
# Mengaitkan objek Bcrypt dengan aplikasi Flask
bcrypt.init_app(app)

# --- Mendaftarkan Blueprint API ---

# Mendaftarkan Blueprint api_bp dengan prefix URL '/api'
# Semua rute di routes.py akan diawali dengan /api
app.register_blueprint(api_bp, url_prefix='/api')

# --- Rute Utama (Opsional) ---

@app.route('/')
def home():
    """Rute dasar untuk memastikan aplikasi berjalan."""
    return jsonify({'message': 'GuardForms Backend API is running smoothly!'}), 200

# --- Bagian Main Aplikasi ---

if __name__ == '__main__':
    # Menggunakan app.app_context() untuk memastikan operasi database berjalan dalam konteks aplikasi.
    with app.app_context():
        # Membuat tabel database jika belum ada
        # Ini akan membaca model dari models.py dan membuat tabel User dan ActivityLog
        db.create_all()
        print("Status Database: Tabel-tabel database berhasil dibuat atau sudah ada.")

        # Memeriksa dan membuat pengguna 'admin' default jika belum ada
        # Ini sangat berguna untuk pengujian awal
        if not db.session.query(db.exists().where(User.username == 'admin')).scalar():
            # Jika pengguna 'admin' belum ada, buat.
            # HASH KATA SANDI: Pastikan menggunakan fungsi hash_password dari auth.py
            admin_password_hash = hash_password('adminpassword123') # <<< GANTI DENGAN KATA SANDI YANG KUAT!
            admin_user = User(username='admin', email='admin@guardforms.com', password_hash=admin_password_hash, role='admin')
            db.session.add(admin_user) # Tambahkan ke sesi
            db.session.commit() # Simpan ke database
            print("Status Pengguna Admin: Pengguna admin default (username: admin, password: adminpassword123) berhasil dibuat.")
        else:
            print("Status Pengguna Admin: Pengguna admin default sudah ada.")

    # Menjalankan aplikasi Flask
    # debug=True: Aktifkan mode debug (reload otomatis, informasi error detail) - HANYA UNTUK PENGEMBANGAN!
    # port=5000: Menjalankan aplikasi di port 5000
    app.run(debug=True, port=5000)