from flask import Blueprint, request, jsonify
from app.chatbot_agent import chat
from app.models import Jadwal, Kursi
from app import db
from datetime import datetime, timedelta
import pytz
import re
import logging

# Setup logging
logger = logging.getLogger(__name__)

chatbot_bp = Blueprint('chatbot_bp', __name__)

@chatbot_bp.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """Main chatbot endpoint"""
    try:
        data = request.get_json() or {}
        message = data.get("message", "").strip()
        history = data.get("chat_history", [])
        
        if not message:
            return jsonify({"status": "error", "response": "Pesan tidak boleh kosong"}), 400
        
        logger.info(f"Incoming chat message: {message}")
        result = chat(message, history)
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "response": "Terjadi kesalahan pada server"}), 500

@chatbot_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Ngulisik Chatbot"}), 200

