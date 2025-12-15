import os
import pandas as pd
from flask import (
    Flask, Response,
    render_template, jsonify,
    request, session, send_from_directory
)

from model.gmail import send_otp

app = Flask(__name__)
app.secret_key = "ielts_listening_generator_secret_key"

# -- Routes --
@app.route("/")
def index():
    return render_template("./frontend/template/index.html")

if __name__ == "__main__":
    app.run(debug=True)