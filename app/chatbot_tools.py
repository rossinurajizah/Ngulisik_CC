"""
Database query tools untuk LangChain Agent Ngulisik
Hanya file ini yang berinteraksi dengan database untuk chatbot
"""
from langchain_core.tools import tool
from app.models import Kursi, Jadwal
from app import db
from datetime import datetime, timedelta
import pytz

tz = pytz.timezone('Asia/Jakarta')

WINDOW_SEATS = {1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 17, 18, 21}

SEAT_POSITIONS = {
    1: "Depan, Kolom Kiri (Dekat Jendela)", 2: "Depan, Kolom Kiri (Dekat Jendela)",
    3: "Depan, Kolom Kiri (Dekat Jendela)", 4: "Depan, Kolom Kanan (Dekat Jendela)",
    5: "Depan, Kolom Kanan (Dekat Jendela)", 6: "Tengah, Sisi Kiri (Dekat Jendela)",
    7: "Tengah, Sisi Kiri (Dekat Lorong)", 8: "Tengah, Sisi Kanan (Dekat Lorong)",
    9: "Tengah, Sisi Kanan (Dekat Jendela)", 10: "Belakang, Sisi Kiri Baris 1 (Dekat Jendela)",
    11: "Belakang, Sisi Kiri Baris 1 (Dekat Lorong)", 12: "Belakang, Sisi Kanan Baris 1 (Dekat Lorong)",
    13: "Belakang, Sisi Kanan Baris 1 (Dekat Jendela)", 14: "Belakang, Sisi Kiri Baris 2 (Dekat Jendela)",
    15: "Belakang, Sisi Kiri Baris 2 (Dekat Lorong)", 16: "Belakang, Sisi Kanan Baris 2 (Dekat Lorong)",
    17: "Belakang, Sisi Kanan Baris 2 (Dekat Jendela)", 18: "Belakang, Sisi Kiri Baris 3 (Dekat Jendela)",
    19: "Belakang, Sisi Kiri Baris 3 (Dekat Lorong)", 20: "Belakang, Sisi Kanan Baris 3 (Dekat Lorong)",
    21: "Belakang, Sisi Kanan Baris 3 (Dekat Jendela)"
}

@tool
def get_schedule_info(jadwal_id: int) -> dict:
    """Get info jadwal: tanggal, waktu, harga, dan jumlah kursi tersedia"""
    try:
        schedule = Jadwal.query.filter(Jadwal.Id_Jadwal == jadwal_id).first()
        
        if not schedule:
            return {"error": "Jadwal tidak ditemukan"}
        
        available_count = Kursi.query.filter(
            Kursi.Id_Jadwal == jadwal_id,
            Kursi.Status_Pemesanan == False
        ).count()
        
        return {
            "id_jadwal": schedule.Id_Jadwal,
            "tanggal": str(schedule.Tanggal),
            "waktu_pemberangkatan": str(schedule.Waktu_Pemberangkatan),
            "waktu_tiba": str(schedule.Waktu_Tiba),
            "harga_per_kursi": float(schedule.Harga) if schedule.Harga else 10000,
            "kursi_tersedia": available_count,
            "status": "Tersedia" if available_count > 0 else "PENUH - Semua kursi terboking"
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


@tool
def get_all_schedules() -> list:
    """
    Get semua jadwal yang tersedia (7 hari ke depan).
    Hanya menampilkan JUMLAH kursi tersedia, bukan detail kursi individual
    """
    try:
        today = datetime.now(tz).date()
        future_date = today + timedelta(days=7)
        
        schedules = Jadwal.query.filter(
            Jadwal.Tanggal >= today,
            Jadwal.Tanggal <= future_date
        ).order_by(Jadwal.Tanggal, Jadwal.Waktu_Pemberangkatan).all()
        
        result = []
        for s in schedules:
            available_count = Kursi.query.filter(
                Kursi.Id_Jadwal == s.Id_Jadwal,
                Kursi.Status_Pemesanan == False
            ).count()
            
            result.append({
                "id_jadwal": s.Id_Jadwal,
                "tanggal": str(s.Tanggal),
                "waktu_pemberangkatan": str(s.Waktu_Pemberangkatan),
                "waktu_tiba": str(s.Waktu_Tiba),
                "harga_per_kursi": float(s.Harga) if s.Harga else 10000,
                "kursi_tersedia": available_count,
                "status": "Tersedia" if available_count > 0 else "PENUH"
            })
        
        return result if result else {"info": "Tidak ada jadwal tersedia"}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


@tool
def recommend_schedule_by_seat_count(jumlah_kursi_dibutuhkan: int) -> list:
    """
    Rekomendasi jadwal yang memiliki kursi tersedia sesuai jumlah yang dibutuhkan user
    Tidak memberikan detail kursi individual, hanya rekomendasi jadwal dengan jumlah kursi yang cukup
    """
    try:
        today = datetime.now(tz).date()
        future_date = today + timedelta(days=7)
        
        schedules = Jadwal.query.filter(
            Jadwal.Tanggal >= today,
            Jadwal.Tanggal <= future_date
        ).order_by(Jadwal.Tanggal, Jadwal.Waktu_Pemberangkatan).all()
        
        result = []
        for s in schedules:
            available_count = Kursi.query.filter(
                Kursi.Id_Jadwal == s.Id_Jadwal,
                Kursi.Status_Pemesanan == False
            ).count()
            
            if available_count >= jumlah_kursi_dibutuhkan:
                result.append({
                    "id_jadwal": s.Id_Jadwal,
                    "tanggal": str(s.Tanggal),
                    "waktu_pemberangkatan": str(s.Waktu_Pemberangkatan),
                    "waktu_tiba": str(s.Waktu_Tiba),
                    "harga_per_kursi": float(s.Harga) if s.Harga else 10000,
                    "kursi_tersedia": available_count,
                    "saran": f"Jadwal ini memiliki {available_count} kursi tersedia (cukup untuk {jumlah_kursi_dibutuhkan} kursi)"
                })
        
        return result if result else {"info": f"Tidak ada jadwal dengan {jumlah_kursi_dibutuhkan} kursi tersedia"}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


CHATBOT_TOOLS = [
    get_schedule_info,
    get_all_schedules,
    recommend_schedule_by_seat_count,
]
