from flask import (
    Flask,
    jsonify,
    render_template,
    request,
)
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "ielts_listening_generator_secret_key"
CORS(app)

# -- Routes --
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)