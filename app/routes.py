from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, flash
from app import db
from app.models import User, Jadwal, Kursi, Pemesanan
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random, string
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import pytz, random, string

routes = Blueprint('routes', __name__)

# ======================================================
#  FORMS
# ======================================================
class RegisterForm(FlaskForm):
    name = StringField('Nama', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    telepon = StringField('Telepon', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password_confirmation = PasswordField('Konfirmasi Password', validators=[DataRequired(), EqualTo('password', message='Password tidak sama')])
    submit = SubmitField('Daftar')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Masuk')

class LogoutForm(FlaskForm):
    submit = SubmitField('Keluar')

@routes.context_processor
def inject_logout_form():
    # Ini akan membuat variable 'logout_form' tersedia di semua template
    return dict(logout_form=LogoutForm())

# ======================================================
#  AUTH: REGISTER
# ======================================================
@routes.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            email=form.email.data,
            telepon=form.telepon.data,
            password=generate_password_hash(form.password.data),
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for('routes.login'))
    return render_template('auth/register.html', form=form)

# ======================================================
#  AUTH: LOGIN
# ======================================================
@routes.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        # Cari user berdasarkan email
        user = User.query.filter_by(email=email).first()
        
        # Validasi email terlebih dahulu
        if not user:
            form.email.errors.append('Email tidak terdaftar')
            return render_template('auth/login.html', form=form)
        
        # Validasi password
        if not check_password_hash(user.password, password):
            form.password.errors.append('Password salah')
            return render_template('auth/login.html', form=form)
        
        # Login berhasil
        login_user(user)
        flash("Berhasil login!", "success")
        return redirect(url_for('routes.home'))
    
    return render_template('auth/login.html', form=form)

# ======================================================
#  AUTH: LOGOUT
# ======================================================
@routes.route('/logout', methods=['POST'])
@login_required
def logout():
    form = LogoutForm()
    if form.validate_on_submit():
        logout_user()
        flash("Berhasil logout.", "info")
    return redirect(url_for('routes.home'))

# ======================================================
# HALAMAN PROFIL USER
# ======================================================
@routes.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user, active_page='profile')

# ======================================================
#  HALAMAN UTAMA (BERANDA)
# ======================================================
@routes.route('/')
def home():
    form = LogoutForm()
    return render_template('home.html', active_page='home', form=form)

# ======================================================
# PESAN TIKET
# ======================================================
@routes.route('/pesan-tiket', methods=['GET', 'POST'])
@login_required
def pesan_tiket():
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)

    tanggal = request.args.get('tanggal') 
    jadwal_list = []

    if tanggal:
        jadwal_list = Jadwal.query.filter_by(Tanggal=tanggal).all()

    return render_template(
        'pesan_tiket.html',
        jadwal_list=jadwal_list,
        tanggal=tanggal,
        now=now
    )

# ======================================================
# PILIH KURSI (Menerima POST dari form pilih kursi, menyimpan ke Session, lalu Redirect GET)
# ======================================================
@routes.route('/pilih-kursi/<int:jadwal_id>', methods=['GET', 'POST'])
@login_required
def pilih_kursi(jadwal_id):
    jadwal = Jadwal.query.get_or_404(jadwal_id)
    kursi_list = Kursi.query.filter_by(Id_Jadwal=jadwal_id).all()
    kursi_list.sort(key=lambda kursi: int(kursi.Nomor_Kursi))
    
    # Ambil kursi yang sudah ada di session (jika user kembali)
    selected_kursi_ids = session.get('selected_kursi', []) 

    if request.method == 'POST':
        # 1. Ambil kursi yang dipilih dari formulir
        # Catatan: Pastikan name di HTML adalah name="kursi[]" atau name="kursi"
        selected_kursi_form = request.form.getlist('kursi[]') or request.form.getlist('kursi')
        
        if not selected_kursi_form:
            flash("Anda harus memilih setidaknya satu kursi.", "warning")
            return redirect(url_for('routes.pilih_kursi', jadwal_id=jadwal_id))

        # 2. Simpan kursi dan jadwal ke session
        session['selected_kursi'] = selected_kursi_form
        session['jadwal_id'] = jadwal_id
        flash(f"{len(selected_kursi_form)} kursi telah dipilih. Lanjut ke konfirmasi.", "success")
        
        # 3. REDIRECT ke halaman konfirmasi (memicu method GET di /konfirmasi-pemesanan)
        return redirect(url_for('routes.konfirmasi_pemesanan'))

    # Untuk method GET, tampilkan halaman pilih kursi
    return render_template(
        'pilih_kursi.html', 
        jadwal=jadwal, 
        kursi_list=kursi_list, 
        selected_kursi=selected_kursi_ids
    )

# ======================================================
# KONFIRMASI PEMESANAN (GET: Tampilkan Ringkasan, POST: Simpan DB)
# ======================================================
@routes.route('/konfirmasi-pemesanan', methods=['GET', 'POST'])
@login_required
def konfirmasi_pemesanan():
    
    jadwal_id = session.get('jadwal_id')
    selected_kursi_ids = session.get('selected_kursi', [])

    if not jadwal_id or not selected_kursi_ids:
        flash("Silakan pilih jadwal dan kursi terlebih dahulu.", "warning")
        return redirect(url_for('routes.pesan_tiket'))

    jadwal = Jadwal.query.get_or_404(jadwal_id)
    
    # Ambil objek kursi agar bisa mendapatkan Nomor_Kursi di template
    kursi_objects = Kursi.query.filter(Kursi.Id_Kursi.in_([int(k_id) for k_id in selected_kursi_ids])).all()
    
    harga_per_kursi = float(jadwal.Harga)
    # Hitung total harga keseluruhan
    total_harga_keseluruhan = harga_per_kursi * len(kursi_objects)

    if request.method == 'POST':
        # **********************************************
        # LOGIKA FINAL PENYIMPANAN KE DATABASE (Tiket Unik per Kursi)
        # **********************************************
        
        booked_tickets_for_session = [] # Akan menyimpan semua detail tiket yang berhasil
        tz = pytz.timezone('Asia/Jakarta')
        tanggal_pemesanan_now = datetime.now(tz)

        try:
            # 1. Loop melalui SETIAP kursi yang dipilih
            for kursi_id in selected_kursi_ids:
                kursi = Kursi.query.get(int(kursi_id))
                
                # Double-check: Pastikan kursi masih tersedia sebelum menyimpan
                if kursi.Status_Pemesanan:
                    # Jika ada kursi yang sudah terisi, batalkan seluruh transaksi
                    db.session.rollback() 
                    flash(f"Kursi {kursi.Nomor_Kursi} sudah terisi saat Anda menekan Bayar. Silakan ulangi pilihan Anda.", "danger")
                    return redirect(url_for('routes.pilih_kursi', jadwal_id=jadwal_id))
                
                # 2. GENERATE KODE TIKET UNIK (Contoh: 6L980AU) UNTUK TIKET INI
                kode_tiket_unik = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                
                # Tandai kursi sebagai terpesan
                kursi.Status_Pemesanan = True
                
                # Buat entri Pemesanan BARU untuk SETIAP kursi (sebagai TIKET UNIK)
                pemesanan = Pemesanan(
                    user_id=current_user.id,
                    Id_Jadwal=jadwal_id,
                    Id_Kursi=kursi.Id_Kursi,
                    Total_Harga=harga_per_kursi,       # Harga per tiket
                    Kode_Pemesanan=kode_tiket_unik,    # Menggunakan Kode Unik per tiket
                    Tanggal_Pemesanan=tanggal_pemesanan_now
                )
                db.session.add(pemesanan)

                # Simpan detail tiket ini untuk halaman struk
                booked_tickets_for_session.append({
                    'kode': kode_tiket_unik,
                    'nomor_kursi': kursi.Nomor_Kursi,
                    'harga': harga_per_kursi
                })

            db.session.commit()
            
            # 3. Siapkan data FINAL untuk halaman Struk
            # Kirim list lengkap tiket ke sesi
            session['struk'] = {
                'total_harga': total_harga_keseluruhan,
                'jadwal_id': jadwal_id,
                'tickets_list': booked_tickets_for_session,
                'tanggal_jadwal': jadwal.Tanggal.strftime('%d %B %Y'),  # ✅ Format untuk tampilan
                'waktu_berangkat': jadwal.Waktu_Pemberangkatan.strftime('%H:%M'),
                'waktu_tiba': jadwal.Waktu_Tiba.strftime('%H:%M'),
                'tanggal_pemesanan': tanggal_pemesanan_now.strftime('%d %B %Y'),  # ✅ TAMBAHKAN INI
                'waktu_pemesanan': tanggal_pemesanan_now.strftime('%H:%M:%S'),     # ✅ Bonus: waktu detail
                'kode_pemesanan': booked_tickets_for_session[0]['kode'] if booked_tickets_for_session else 'N/A'  # ✅ Kode pemesanan utama
            }

            # Hapus data sesi transaksional
            session.pop('selected_kursi', None)
            session.pop('jadwal_id', None)
            
            flash("Pemesanan berhasil! Silakan cetak struk Anda.", "success")
            return redirect(url_for('routes.struk'))

        except Exception as e:
            db.session.rollback()
            # Log error: print(e)
            flash(f"Terjadi kesalahan saat memproses pesanan: {e}", "danger")
            return redirect(url_for('routes.pesan_tiket'))


    # Jika method GET (Menampilkan halaman konfirmasi/ringkasan)
    return render_template('konfirmasi_pemesanan.html',
                            jadwal=jadwal,
                            kursi_selected=kursi_objects, 
                            harga_per_kursi=harga_per_kursi,
                            total_harga=total_harga_keseluruhan) # Gunakan total_harga_keseluruhan

# ======================================================
# STRUK / TIKET
# ======================================================
@routes.route('/struk')
@login_required
def struk():
    struk = session.get('struk')
    if not struk:
        flash("Tidak ada struk tersedia.", "warning")
        return redirect(url_for('routes.pesan_tiket'))

    jadwal = Jadwal.query.get(struk['jadwal_id'])
    return render_template('struk.html', struk=struk, jadwal=jadwal)

# ======================================================
#  HALAMAN HARGA TIKET
# ======================================================
@routes.route('/harga-tiket')
def harga_tiket():
    form = LogoutForm()
    return render_template('harga_tiket.html', active_page='harga_tiket', form=form)

# ======================================================
#  HALAMAN JADWAL KEBERANGKATAN
# ======================================================
@routes.route('/jadwal-keberangkatan')
def jadwal_keberangkatan():
    form = LogoutForm()
    return render_template('jadwal_keberangkatan.html', active_page='jadwal_keberangkatan', form=form)

# ======================================================
#  HALAMAN RUTE PERJALANAN
# ======================================================
@routes.route('/rute-perjalanan')
def rute_perjalanan():
    form = LogoutForm()
    return render_template('rute_perjalanan.html', active_page='rute_perjalanan', form=form)

# ======================================================
#  HALAMAN FASILITAS
# ======================================================
@routes.route('/fasilitas')
def fasilitas():
    form = LogoutForm()
    return render_template('fasilitas.html', active_page='fasilitas', form=form)

# ======================================================
#  MENU PESANAN SAYA
# ======================================================
@routes.route('/pesanan')
@login_required
def pesanan():
    form = LogoutForm()
    pemesanan = Pemesanan.query.filter_by(user_id=current_user.id).all()
    return render_template('pesanan.html', pemesanan=pemesanan, form=form)

# ======================================================
#  HALAMAN TENTANG
# ======================================================
@routes.route('/tentang')
def tentang():
    form = LogoutForm()
    return render_template('tentang.html', form=form)


# ----------------------------
#       DASHBOARD ADMIN
# ----------------------------

@routes.route('/admin')
def admin_dashboard():
    total_jadwal = Jadwal.query.count()
    total_pemesanan = Pemesanan.query.count() if 'Pemesanan' in globals() else 0
    total_users = User.query.count() if 'User' in globals() else 0

    return render_template(
        'admin/dashboard.html',
        total_jadwal=total_jadwal,
        total_pemesanan=total_pemesanan,
        total_users=total_users
    )


# ----------------------------
#        JADWAL
# ----------------------------

@routes.route('/admin/jadwal')
def admin_jadwal_list():
    data = Jadwal.query.order_by(Jadwal.Tanggal.asc()).all()
    return render_template('admin/jadwal_list.html', data=data)


@routes.route('/admin/jadwal/tambah', methods=['GET', 'POST'])
def admin_jadwal_tambah():
    if request.method == 'POST':
        tanggal = request.form['tanggal']
        jam = request.form['jam']
        harga = request.form['harga']

        j = Jadwal(
            Tanggal=tanggal,
            Waktu_Pemberangkatan=jam,
            Waktu_Tiba=jam,   # sementara (atau buat field input baru)
            Harga=harga,
            Kursi_Tersedia=30
        )
        db.session.add(j)
        db.session.commit()

        flash("Jadwal berhasil ditambahkan!", "success")
        return redirect(url_for('routes.admin_jadwal_list'))

    return render_template('admin/jadwal_tambah.html')


@routes.route('/admin/jadwal/edit/<int:id>', methods=['GET', 'POST'])
def admin_jadwal_edit(id):
    jadwal = Jadwal.query.get_or_404(id)

    if request.method == 'POST':
        jadwal.Tanggal = request.form['tanggal']
        jadwal.Waktu_Pemberangkatan = request.form['jam']
        jadwal.Harga = request.form['harga']

        db.session.commit()
        flash("Jadwal berhasil diperbarui!", "success")
        return redirect(url_for('routes.admin_jadwal_list'))

    return render_template('admin/jadwal_edit.html', jadwal=jadwal)


@routes.route('/admin/jadwal/hapus/<int:id>')
def admin_jadwal_hapus(id):
    jadwal = Jadwal.query.get_or_404(id)
    db.session.delete(jadwal)
    db.session.commit()

    flash("Jadwal berhasil dihapus!", "warning")
    return redirect(url_for('routes.admin_jadwal_list'))


# ----------------------------
#        KURSI
# ----------------------------

@routes.route('/admin/kursi')
def admin_kursi_list():
    data = Kursi.query.all() if 'Kursi' in globals() else []
    return render_template('admin/kursi_list.html', data=data)


# ----------------------------
#    DAFTAR PEMESANAN
# ----------------------------

@routes.route('/admin/pemesanan')
def admin_pemesanan_list():
    data = Pemesanan.query.order_by(Pemesanan.Id_Pemesanan.desc()).all() if 'Pemesanan' in globals() else []
    return render_template('admin/pemesanan_list.html', data=data)


# ----------------------------
#    DAFTAR USER
# ----------------------------

@routes.route('/admin/users')
def admin_users_list():
    data = User.query.all() if 'User' in globals() else []
    return render_template('admin/users_list.html', data=data)


# ----------------------------
#    CHATBOT
# ----------------------------

@routes.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html")
