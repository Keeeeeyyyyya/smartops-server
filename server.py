from flask import Flask, request, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

# Store latest live state
table_states = {}
total_calls_count = 0

# Create CSV file automatically
if not os.path.exists("logs.csv"):
    with open("logs.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Time", "Table", "Event"])


# ==========================================
# RECEIVE EVENTS FROM ESP
# ==========================================
@app.route("/log", methods=["POST"])
def log_event():

    data = request.json

    table_id = data.get("tableId")
    event = data.get("event")
    icon = data.get("icon")
    time_str = data.get("time")

    if not table_id or not event:
        return jsonify({"error": "Invalid data"}), 400
    global total_calls_count
    total_calls_count += 1

    # Update latest table status
    table_states[table_id] = {
        "table_id": table_id,
        "status": event,
        "icon": icon,
        "time": time_str,
        "updated_at": datetime.now()
    }

    # Save FULL history permanently
    with open("logs.csv", "a", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            datetime.now().strftime("%d-%m-%Y"),
            datetime.now().strftime("%H:%M:%S"),
            table_id,
            event
        ])

    return jsonify({
        "status": "success"
    }), 200


# ==========================================
# SEND DATA TO FLET DASHBOARD
# ==========================================
@app.route("/data", methods=["GET"])
def get_data():

    live_status = []

    total_calls = 0
    open_calls = 0

    for table in table_states.values():

        minutes_ago = int(
            (datetime.now() - table["updated_at"]).total_seconds() / 60
        )

        live_status.append({
            "table_id": table["table_id"],
            "status": table["status"],
            "minutes_ago": minutes_ago
        })

        total_calls += 1

        if table["status"] != "Table_Closed":
            open_calls += 1

    return jsonify({
        "live_status": live_status,
        "analytics": {
            "total": total_calls,
            "open": open_calls
        }
    })


# ==========================================
# START SERVER
# ==========================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)