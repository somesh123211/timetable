from flask import Blueprint, request, jsonify
from config.db import get_db_connection
import bcrypt

auth_bp = Blueprint('auth', __name__)

def generate_username(name):
    return name.lower().replace(" ", ".")


# ================= REGISTER =================
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json

    name = data.get("name")
    department_name = data.get("department")
    password = data.get("password")

    if not name or not department_name or not password:
        return jsonify({"error": "All fields required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get dept
        cursor.execute("SELECT id FROM departments WHERE name=%s", (department_name,))
        dept = cursor.fetchone()

        if not dept:
            return jsonify({"error": "Department not found"}), 404

        dept_id = dept["id"]

        # Insert faculty
        cursor.execute("INSERT INTO faculty (name, dept_id) VALUES (%s, %s)", (name, dept_id))
        faculty_id = cursor.lastrowid

        username = generate_username(name)

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        cursor.execute("""
            INSERT INTO users (username, password, role, faculty_id, dept_id)
            VALUES (%s, %s, 'faculty', %s, %s)
        """, (username, hashed_password, faculty_id, dept_id))

        conn.commit()

        return jsonify({
            "message": "Registered successfully",
            "username": username
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    username = data.get("username")
    password = data.get("password")

    # ✅ Validation
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 🔍 Fetch user
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        # ❌ User not found
        if not user:
            return jsonify({"error": "User not found"}), 404

        # 🔐 Password check
        if bcrypt.checkpw(
            password.encode('utf-8'),
            user['password'].encode('utf-8')
        ):
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "faculty_id": user["faculty_id"],
                    "dept_id": user["dept_id"]
                }
            })
        else:
            return jsonify({"error": "Invalid password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500