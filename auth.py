import jwt
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from models import db, User
from config import Config

bcrypt = Bcrypt()

def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

def check_password(hashed_password, password):
    return bcrypt.check_password_hash(hashed_password, password)

def generate_token(user_id, role):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
        'sub': str(user_id),
        'role': role
    }
    print("\n=== DEBUG ENCODE ===")
    print(f"SECRET_KEY saat encode: '{Config.SECRET_KEY}'")
    print(f"Payload yang akan di-encode: {payload}")

    token = jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')

    
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    print(f"Token yang dihasilkan: '{token}'")
    print("=== END DEBUG ENCODE ===\n")
    return token

def decode_token(token):
    print("\n=== DEBUG DECODE ===")
    print(f"Token diterima untuk decode: '{token}'")
    print(f"SECRET_KEY saat decode: '{Config.SECRET_KEY}'")
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        print(f"Hasil payload decode: {payload}")
        print("=== END DEBUG DECODE ===\n")
        return payload
    except jwt.ExpiredSignatureError:
        print("Token kadaluarsa.")
        return {'message': 'Token kadaluarsa. Silakan login kembali.'}
    except jwt.InvalidTokenError as e:
        print(f"Token tidak valid: {str(e)}")
        return {'message': 'Token tidak valid. Autentikasi gagal.'}
    except Exception as e:
        print(f"Terjadi kesalahan tak terduga: {str(e)}")
        return {'message': f'Terjadi kesalahan saat mendekode token: {str(e)}'}

def register_user(username, email, password, role='viewer'):
    hashed_password = hash_password(password)
    new_user = User(username=username, email=email, password_hash=hashed_password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def login_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password(user.password_hash, password):
        token = generate_token(user.id, user.role)
        return user, token
    return None, None
