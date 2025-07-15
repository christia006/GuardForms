from flask import request, jsonify, Blueprint
from functools import wraps # Digunakan untuk menjaga metadata fungsi asli
from auth import register_user, login_user, decode_token # Import fungsi otentikasi
from models import db, User, ActivityLog # Import model database
from datetime import datetime

# Membuat Blueprint untuk mengelompokkan rute-rute API
api_bp = Blueprint('api', __name__)

# --- Decorator untuk Otentikasi dan Otorisasi ---

def token_required(f):
    """
    Decorator yang memastikan request memiliki token JWT yang valid.
    Jika valid, objek User saat ini akan diteruskan ke fungsi.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Periksa apakah header Authorization ada dan berformat 'Bearer <token>'
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({'message': 'Format token tidak valid. Gunakan: Bearer <token>'}), 401

        if not token:
            return jsonify({'message': 'Token autentikasi tidak ditemukan. Silakan login.'}), 401

        try:
            data = decode_token(token) # Dekode token
            if 'message' in data: # Jika ada pesan error dari decode_token (misal: kadaluarsa)
                return jsonify({'message': data['message']}), 401

            # Cari pengguna berdasarkan ID dari token
            current_user = User.query.get(data['sub'])
            if not current_user:
                return jsonify({'message': 'Pengguna tidak ditemukan berdasarkan token.'}), 401
        except Exception as e:
            # Tangani kesalahan tak terduga selama decoding token
            return jsonify({'message': f'Token tidak valid atau terjadi kesalahan: {str(e)}'}), 401

        # Teruskan objek pengguna saat ini ke fungsi rute
        return f(current_user, *args, **kwargs)
    return decorated

def roles_required(roles):
    """
    Decorator yang memastikan pengguna memiliki salah satu peran yang dibutuhkan.
    Harus digunakan setelah @token_required.
    """
    def wrapper(fn):
        @wraps(fn)
        @token_required # Memastikan token sudah diverifikasi terlebih dahulu
        def decorator(current_user, *args, **kwargs): # current_user sudah disediakan oleh @token_required
            if current_user.role not in roles:
                return jsonify({'message': f'Akses ditolak: Anda tidak memiliki peran yang sesuai. Dibutuhkan peran: {", ".join(roles)}'}), 403
            return fn(current_user, *args, **kwargs)
        return decorator
    return wrapper

# --- Endpoint API Autentikasi ---

@api_bp.route('/register', methods=['POST'])
def register():
    """Endpoint untuk mendaftarkan pengguna baru."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'viewer') # Role default adalah 'viewer'

    # Validasi input dasar
    if not username or not email or not password:
        return jsonify({'message': 'Semua field (username, email, password) harus diisi.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username sudah digunakan. Pilih username lain.'}), 409 # Conflict
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email sudah terdaftar. Gunakan email lain.'}), 409 # Conflict

    try:
        new_user = register_user(username, email, password, role)
        return jsonify({'message': f'Pengguna {new_user.username} berhasil didaftarkan!', 'user_id': new_user.id}), 201 # Created
    except Exception as e:
        db.session.rollback() # Batalkan transaksi jika ada kesalahan
        return jsonify({'message': f'Gagal mendaftarkan pengguna: {str(e)}'}), 500 # Internal Server Error

@api_bp.route('/login', methods=['POST'])
def login():
    """Endpoint untuk login pengguna dan mendapatkan token JWT."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username dan password harus diisi.'}), 400

    user, token = login_user(username, password)

    if user and token:
        # Catat aktivitas login ke ActivityLog
        log = ActivityLog(user_id=user.id, action='User Login', details=f'Pengguna {user.username} (ID: {user.id}) berhasil login.')
        db.session.add(log)
        db.session.commit()
        return jsonify({
            'message': 'Login berhasil!',
            'token': token, # Token JWT yang perlu disimpan oleh client
            'user_id': user.id,
            'username': user.username,
            'role': user.role
        }), 200
    else:
        return jsonify({'message': 'Kredensial tidak valid. Periksa username dan password Anda.'}), 401 # Unauthorized

# --- Endpoint Khusus ---

@api_bp.route('/dashboard', methods=['GET'])
@token_required # Hanya pengguna dengan token valid yang bisa mengakses
def dashboard(current_user):
    """Endpoint contoh untuk dashboard pengguna, hanya bisa diakses setelah login."""
    return jsonify({
        'message': f'Selamat datang di dashboard Anda, {current_user.username}!',
        'user_id': current_user.id,
        'email': current_user.email,
        'role': current_user.role,
        'login_time': datetime.utcnow().isoformat() + 'Z' # Contoh informasi tambahan
    }), 200

@api_bp.route('/admin/users', methods=['GET'])
@roles_required(['admin']) # Hanya pengguna dengan peran 'admin' yang bisa mengakses
def get_all_users(current_user):
    """Endpoint untuk admin melihat daftar semua pengguna."""
    users = User.query.all()
    output = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat() + 'Z'
        }
        output.append(user_data)
    return jsonify({'users': output}), 200

@api_bp.route('/admin/audit_logs', methods=['GET'])
@roles_required(['admin', 'moderator']) # Admin dan moderator bisa melihat log audit
def get_audit_logs(current_user):
    """Endpoint untuk admin/moderator melihat semua log aktivitas."""
    # Urutkan log dari yang terbaru
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    output = []
    for log in logs:
        log_data = {
            'id': log.id,
            'user_id': log.user_id,
            'username': log.user.username if log.user else 'N/A (User Deleted)', # Ambil username dari relasi
            'action': log.action,
            'timestamp': log.timestamp.isoformat() + 'Z',
            'details': log.details
        }
        output.append(log_data)
    return jsonify({'audit_logs': output}), 200

# --- Endpoint Simulasi Sinkronisasi Data ---

@api_bp.route('/sync/google_forms', methods=['POST'])
@roles_required(['admin', 'moderator']) # Admin dan moderator bisa melakukan sinkronisasi
def sync_google_forms(current_user):
    """
    Endpoint placeholder untuk mensimulasikan sinkronisasi data dari Google Forms.
    Di sini Anda akan mengintegrasikan logika sebenarnya untuk memproses data.
    """
    data = request.get_json()
    form_data = data.get('form_data') # Ini adalah contoh data yang diharapkan dari Google Forms

    if not form_data:
        return jsonify({'message': 'Tidak ada data Google Forms yang disediakan untuk disinkronkan.'}), 400

    # --- Logika Simulasi Pemrosesan Data Google Forms ---
    # Di sini Anda akan menambahkan logika untuk:
    # 1. Validasi struktur form_data.
    # 2. Mengubah form_data agar sesuai dengan skema database Anda (misalnya, tabel peserta).
    # 3. Menyimpan data yang sudah diproses ke tabel database yang relevan (misalnya, tabel peserta).
    # 4. Menangani data duplikat atau pembaruan data yang sudah ada.
    # Contoh: Simpan ke tabel 'Participants' jika Anda memiliki model untuk itu.
    # from models import Participant # Anda perlu membuat model Participant di models.py

    try:
        # Simulasi menyimpan data (misalnya, log saja)
        log_details = f"Data Google Forms diterima untuk sinkronisasi. Diterima oleh: {current_user.username}. Cuplikan data: {str(form_data)[:200]}..."
        log = ActivityLog(user_id=current_user.id, action='Google Forms Sync (Simulated)', details=log_details)
        db.session.add(log)
        db.session.commit()

        # Di sini Anda bisa mengimplementasikan logika untuk memicu peringatan otomatis
        # Misalnya, jika ada anomali dalam data yang disinkronkan.
        # if 'suspicious_field' in form_data:
        #     # Kirim peringatan ke admin
        #     pass

        return jsonify({'message': 'Data Google Forms berhasil disinkronkan (simulasi). Log aktivitas dicatat.', 'received_data': form_data}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Gagal mensinkronkan data Google Forms: {str(e)}'}), 500