from app import db
from flask_login import UserMixin
from datetime import datetime
import pytz

# timezone WIB
tz = pytz.timezone('Asia/Jakarta')

# ============================
# USERS
# ============================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    telepon = db.Column(db.String(16), nullable=False)
    role = db.Column(db.String(255), default='user')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz))

    pemesanan = db.relationship('Pemesanan', backref='user', lazy=True)


# ============================
# JADWAL
# ============================
class Jadwal(db.Model):
    __tablename__ = 'jadwal'

    Id_Jadwal = db.Column(db.Integer, primary_key=True)
    Waktu_Pemberangkatan = db.Column(db.Time)
    Waktu_Tiba = db.Column(db.Time)
    Harga = db.Column(db.Numeric(10, 0))
    Kursi_Tersedia = db.Column(db.Integer)
    Tanggal = db.Column(db.Date)

    kursi = db.relationship('Kursi', backref='jadwal', lazy=True)
    pemesanans = db.relationship('Pemesanan', back_populates='jadwal', lazy=True)


# ============================
# KURSI
# ============================
class Kursi(db.Model):
    __tablename__ = 'kursi'

    Id_Kursi = db.Column(db.Integer, primary_key=True)
    Id_Jadwal = db.Column(db.Integer, db.ForeignKey('jadwal.Id_Jadwal'), nullable=False)
    Nomor_Kursi = db.Column(db.String(60))
    Status_Pemesanan = db.Column(db.Boolean)

    pemesanans = db.relationship('Pemesanan', back_populates='kursi', lazy=True)


# ============================
# PEMESANAN
# ============================
class Pemesanan(db.Model):
    __tablename__ = 'pemesanan'

    Id_Pemesanan = db.Column(db.Integer, primary_key=True)
    Kode_Pemesanan = db.Column(db.String(10), nullable=True, unique=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    Id_Jadwal = db.Column(db.Integer, db.ForeignKey('jadwal.Id_Jadwal'))
    Id_Kursi = db.Column(db.Integer, db.ForeignKey('kursi.Id_Kursi'))

    Tanggal_Pemesanan = db.Column(db.DateTime, default=lambda: datetime.now(tz))
    Total_Harga = db.Column(db.Numeric(10, 0))

    jadwal = db.relationship('Jadwal', back_populates='pemesanans')
    kursi = db.relationship('Kursi', back_populates='pemesanans')

    def __repr__(self):
        return f"<Pemesanan {self.Id_Pemesanan} ({self.Kode_Pemesanan}) - Kursi: {self.Id_Kursi}>"
