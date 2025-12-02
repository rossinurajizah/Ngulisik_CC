# run.py

import os
# from dotenv import load_dotenv # <-- TIDAK PERLU DI SINI KARENA SUDAH DI app/__init__.py
from app import create_app

# --- load_dotenv() DIHAPUS DARI SINI ---

app = create_app()

if __name__ == '__main__':
    # Mengambil PORT dari environment variable (untuk deployment), default ke 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)