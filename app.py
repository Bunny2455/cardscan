from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3
import qrcode
import os
from flask_cors import CORS  # Add this import

# Load API URL from Render environment variables
API_BASE = os.getenv("API_BASE")
SITE_UBA = os.getenv("SITE_UBA")

app = Flask(__name__, template_folder="templates", static_folder="static")

# Allow only your frontend domain
CORS(app, resources={r"/*": {"origins": "https://cardscan-nh7d.onrender.com"}})

# Ensure QR Code folder exists
qr_folder = os.path.join("static", "qrcodes") 

# Database initialization
DB_FILE = "bus_fare.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            admission_number TEXT PRIMARY KEY,
            name TEXT,
            place TEXT,
            branch TEXT,
            semester TEXT,
            fixed_fare INTEGER,
            total_fare INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Ensure database exists on startup

def generate_qr(admission_number):
    qr_path = os.path.join(qr_folder, f"{admission_number}.png")
    os.makedirs(qr_folder, exist_ok=True)  # Ensure folder exists

    qr = qrcode.make(admission_number)
    qr.save(qr_path)
    
    return f"/static/qrcodes/{admission_number}.png"  # Return relative path

def add_default_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    default_users = [
        ("222001", "Aaron", "Vengeri", "CSE", 8, 250, 0),
        ("222002", "Jose", "Kuttyadi", "ECE", 4, 300, 0),
        ("222003", "Samariya", "Koomully", "IT", 6, 150, 0)
    ]

    for user in default_users:
        cursor.execute("SELECT * FROM users WHERE admission_number = ?", (user[0],))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", user)

    conn.commit()
    conn.close()

@app.route('/qrcodes/<path:filename>')
def serve_qr_code(filename):
    return send_from_directory("static/qrcodes", filename)

@app.route('/get_api_url')
def get_api_url():
    return jsonify({"api_url": os.getenv("API_BASE")})

@app.route('/get_site_url')
def get_site_url():
    return jsonify({"site_url": os.getenv("SITE_UBA")})

@app.route("/")
def home():
    return render_template("index.html")  # Serve frontend

@app.route("/admin")
def admin():
    return render_template("admin.html")  # Check if 'admin.html' exists

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html") # Check if 'dashboard.html' exists

@app.route("/get_users", methods=["GET"])
def get_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    
    users_list = [
        {
            "admission_number": user[0],
            "name": user[1],
            "place": user[2],
            "branch": user[3],
            "semester": user[4],
            "fixed_fare": user[5],
            "total_fare": user[6],
            "qr_code": f"{request.host_url}static/qrcodes/{user[0]}.png"  # Add QR code URL
        }
        for user in users
    ]
    return jsonify(users_list)

@app.route("/add_user", methods=["POST"])
def add_user():
    try:
        data = request.json  # Ensure JSON is received
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400  # Bad Request

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (admission_number, name, place, branch, semester, fixed_fare, total_fare)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data["admission_number"], data["name"], data["place"], data["branch"], data["semester"], data["fixed_fare"], 0))

        conn.commit()
        conn.close()
        
        qr_path = generate_qr(data["admission_number"])
        print(f"✅ QR Code saved at: {qr_path}")

        return jsonify({"message": "User added successfully", "qr_path": qr_path})

    except Exception as e:
        print(f"❌ Error in /add_user: {e}")  # Log the error
        return jsonify({"error": "Internal Server Error"}), 500  # Return proper error response

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = request.json
    admission_number = data.get("admission_number")

    if not admission_number:
        return jsonify({"error": "Missing admission number"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Delete the user
    cursor.execute("DELETE FROM users WHERE admission_number = ?", (admission_number,))
    conn.commit()
    conn.close()

    return jsonify({"message": "User deleted successfully"})

@app.route("/scan_qr", methods=["POST"])
def scan_qr():
    data = request.json
    admission_number = data["admission_number"]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT name, fixed_fare, total_fare FROM users WHERE admission_number = ?", (admission_number,))
    user = cursor.fetchone()

    if user:
        new_total = user[2] + user[1]
        cursor.execute("UPDATE users SET total_fare = ? WHERE admission_number = ?", (new_total, admission_number))
        conn.commit()
        conn.close()
        print(f"✅message: Scanned {user[0]} successfully, total: {new_total}")
        return jsonify({"message": f"Scanned {user[0]} successfully", "total_fare": new_total})
    
    conn.close()
    return jsonify({"error": "QR Code not found"}), 404

@app.route("/reset_fare", methods=["POST"])
def reset_fare():
    data = request.json
    admission_number = data.get("admission_number")

    if not admission_number:
        return jsonify({"error": "Missing admission number"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Reset total fare to 0
    cursor.execute("UPDATE users SET total_fare = 0 WHERE admission_number = ?", (admission_number,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Fare reset successfully"})

add_default_users()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render provides PORT
    app.run(host="0.0.0.0", port=port, debug=True)
