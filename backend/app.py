from flask import Flask, request, jsonify
from flask_cors import CORS
from timetable_core import generate_timetable

app = Flask(__name__)

# ✅ FIX CORS PROPERLY
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json

    subjects = data.get("subjects", [])
    existing = data.get("existing_timetables", [])   # 🔥 NEW

    print("Subjects:", len(subjects))
    print("Existing Timetables:", len(existing))     # 🔍 DEBUG

    timetable = generate_timetable(subjects, existing)  # 🔥 UPDATED

    return jsonify({"timetable": timetable})


@app.route("/save-timetable", methods=["POST"])
def save_timetable():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)