from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user' # Nama tabel di database
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # Role pengguna: 'admin', 'moderator', 'viewer'. Default 'viewer'.
    role = db.Column(db.String(20), default='viewer', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Waktu pembuatan akun

    # Representasi string dari objek User, berguna untuk debugging
    def __repr__(self):
        return f'<User {self.username} (Role: {self.role})>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_log' # Nama tabel di database
    id = db.Column(db.Integer, primary_key=True)
    # Kunci asing ke tabel User, menunjukkan siapa yang melakukan aktivitas
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False) # Deskripsi singkat aktivitas (misal: 'User Login', 'Data Edited')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Waktu aktivitas terjadi
    details = db.Column(db.Text, nullable=True) # Detail lebih lanjut tentang aktivitas (misal: 'Peserta ID 123 diubah')

   
    user = db.relationship('User', backref='activity_logs')

    def __repr__(self):
        return f'<ActivityLog {self.action} by User {self.user_id} at {self.timestamp}>'