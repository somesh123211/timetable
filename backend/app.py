from flask import Flask
from flask_cors import CORS
from routes.auth_routes import auth_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/auth")

@app.route("/")
def home():
    return {"message": "Backend Running ✅"}

from routes.subject_routes import subject_bp
app.register_blueprint(subject_bp, url_prefix="/subjects")

if __name__ == "__main__":
    app.run(debug=True)