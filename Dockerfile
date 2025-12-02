# Menggunakan base image Python 3.12 slim
FROM python:3.12-slim

# Tetapkan direktori kerja
WORKDIR /app

# Salin requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi Anda
COPY . .

# Konfigurasi Gunicorn (Cloud Run memerlukan listening di $PORT)
ENV PORT 8080 

# Perintah untuk menjalankan Gunicorn
# 'run:app' merujuk pada file run.py dan instance Flask 'app'
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "run:app"]