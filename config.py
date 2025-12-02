import os

class Config:
    # Kunci rahasia tetap sama
    SECRET_KEY = 'ngulisik123'
    
    # URL Koneksi Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Variabel Lingkungan Lain (DIPINDAHKAN KE DALAM KELAS)
    # Catatan: Variabel ini harus bernama GOOGLE_API_KEY di .env
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY","")

    # === PENAMBAHAN UNTUK MENGATASI OPERATIONAL ERROR ===
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 3600, 
        "pool_pre_ping": True 
    }
    # ===================================================