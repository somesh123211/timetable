from flask import Blueprint, request, jsonify
from config.db import get_db_connection

subject_bp = Blueprint('subject', __name__)

@subject_bp.route("/add", methods=["POST"])
def add_subject():
    data = request.json

    name = data.get("name")
    type_ = data.get("type")
    theory_hours = data.get("theory_hours")
    lab_hours = data.get("lab_hours")

    if not name:
        return jsonify({"error": "Subject name required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO subjects (name, type, theory_hours, lab_hours)
            VALUES (%s, %s, %s, %s)
        """, (name, type_, theory_hours, lab_hours))

        conn.commit()

        return jsonify({"message": "Subject added successfully"})

    except Exception as e:
        return jsonify({"error": str(e)})