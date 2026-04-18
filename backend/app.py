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
    timetable = generate_timetable(subjects)
    return jsonify({"timetable": timetable})


@app.route("/save-timetable", methods=["POST"])
def save_timetable():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)