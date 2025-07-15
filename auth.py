import jwt
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from flask import current_app # Digunakan untuk mengakses app.config
from models import db, User # Mengimpor db dan model User dari models.py

# Inisialisasi Bcrypt. Inisialisasi penuh akan dilakukan di app.py
bcrypt = Bcrypt()

def hash_password(password):
    """Mengubah kata sandi plaintext menjadi hash Bcrypt."""
    # .decode('utf-8') diperlukan karena generate_password_hash mengembalikan bytes
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    """Memverifikasi apakah kata sandi plaintext cocok dengan hash yang disimpan."""
    return bcrypt.check_password_hash(hashed_password, password)

def generate_token(user_id, role):
    """Membuat JSON Web Token (JWT) untuk pengguna."""
    payload = {
        'exp': datetime.utcnow() + timedelta(hours=24), # Token kedaluwarsa dalam 24 jam
        'iat': datetime.utcnow(), # Waktu pembuatan token
        'sub': user_id, # Subjek (ID pengguna)
        'role': role # Peran pengguna
    }
    # Menggunakan SECRET_KEY dari konfigurasi aplikasi
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    """Mendekode JWT dan mengembalikan payload atau pesan kesalahan."""
    try:
        # Mendekode token menggunakan SECRET_KEY dan algoritma yang sama
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'message': 'Token kadaluarsa. Silakan login kembali.'}
    except jwt.InvalidTokenError:
        return {'message': 'Token tidak valid. Autentikasi gagal.'}
    except Exception as e:
        return {'message': f'Terjadi kesalahan saat mendekode token: {str(e)}'}

def register_user(username, email, password, role='viewer'):
    """Mendaftarkan pengguna baru ke database."""
    # Hash kata sandi sebelum menyimpannya
    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_password, role=role)
    db.session.add(new_user) # Menambahkan pengguna ke sesi database
    db.session.commit() # Menyimpan perubahan ke database
    return new_user

def login_user(username, password):
    """Memverifikasi kredensial pengguna dan mengembalikan pengguna dan token JWT."""
    user = User.query.filter_by(username=username).first() # Mencari pengguna berdasarkan username
    if user and check_password(user.password_hash, password):
        # Jika pengguna ditemukan dan kata sandi cocok, buat token
        token = generate_token(user.id, user.role)
        return user, token
    return None, None # Jika kredensial tidak valid