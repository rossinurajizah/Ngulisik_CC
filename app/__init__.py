import os
from dotenv import load_dotenv # <-- Import library
# -----------------------------------------------------------
# --- WAJIB: Memuat Environment Variables DI SINI ---
# Ini harus dieksekusi sebelum import Config, 
# agar os.environ.get('DATABASE_URL') memiliki nilai saat Config dievaluasi.
load_dotenv()
# ---------------------------------------------------

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config # <-- Import Config sekarang aman
from flask_migrate import Migrate

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
print("KEY:", GOOGLE_API_KEY)

# Inisialisasi ekstensi secara global
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'routes.login'
login_manager.login_message_category = 'warning'
csrf = CSRFProtect()

def create_app():
    # load_dotenv() TELAH DIHAPUS DARI SINI
    
    app = Flask(__name__)
    # app.config.from_object(Config) sekarang membaca DATABASE_URL dari os.environ
    app.config.from_object(Config)

    # Nonaktifkan CSRF untuk UAS
    app.config['WTF_CSRF_ENABLED'] = False

    # inisialisasi database
    db.init_app(app) # <-- Baris ini seharusnya TIDAK error lagi

    # Inisialisasi Flask-Migrate
    migrate = Migrate(app, db)
    
    # inisialisasi Flask-Login
    login_manager.init_app(app)

    # inisialisasi CSRF
    csrf.init_app(app)

    # import model di sini supaya login_manager bisa load user
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        # Flask-Login membutuhkan user_id dalam bentuk int
        return User.query.get(int(user_id))

    # register blueprint
    from app.routes import routes
    app.register_blueprint(routes)

    from app.chatbot_routes import chatbot_bp
    app.register_blueprint(chatbot_bp)

    return app