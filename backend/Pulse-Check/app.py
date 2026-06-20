import threading

from flask import Flask, jsonify, request # type: ignore
from datetime import datetime, timezone

app = Flask(__name__)
monitors = {}

@app.get("/")
def health_check():
    return jsonify({"message": "Pulse-Check API is running"})

@app.post("/monitors")
def create_monitor():
    data = request.get_json()

    required_fields = ["id", "timeout", "alert_email"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    monitor_id = data["id"]

    if monitor_id in monitors:
        return jsonify({"error": "Monitor already exists"}), 409

    monitor = {
        "id": monitor_id,
        "timeout": data["timeout"],
        "alert_email": data["alert_email"],
        "status": "up",
        "timer": None,
        "last_heartbeat_at": None
    }

    monitors[monitor_id] = monitor
    start_monitor_timer(monitor_id)
    monitor["last_heartbeat_at"] = datetime.now(timezone.utc).isoformat()

    return jsonify({
        "message": f"Monitor {monitor_id} created successfully",
        "monitor": {
            "id": monitor["id"],
            "timeout": monitor["timeout"],
            "alert_email": monitor["alert_email"],
            "status": monitor["status"],
            "last_heartbeat_at": monitor["last_heartbeat_at"]
        }
    }), 201

@app.post("/monitors/<monitor_id>/heartbeat")
def heartbeat(monitor_id):
    if monitor_id not in monitors:
        return jsonify({"error": "Monitor not found"}), 404
    
    monitor = monitors[monitor_id]

    monitor["status"] = "up"
    monitor["last_heartbeat_at"] = datetime.now(timezone.utc).isoformat()
    start_monitor_timer(monitor_id)

    return jsonify({
        "message": f"Heartbeat received for monitor {monitor_id}",
        "monitor": {
            "id": monitor["id"],
            "timeout": monitor["timeout"],
            "alert_email": monitor["alert_email"],
            "status": monitor["status"],
            "last_heartbeat_at": monitor["last_heartbeat_at"]
        }
    }), 200

def fire_alert(monitor_id):
    if monitor_id not in monitors:
        return
    
    monitor = monitors[monitor_id]
    monitor["status"] = "down"
    monitor["timer"] = None

    print({
        "ALERT": f"Device {monitor_id} is down!",
        "time": datetime.now(timezone.utc).isoformat(),
        "alert_email": monitor["alert_email"]
    })

def start_monitor_timer(monitor_id):
    monitor = monitors[monitor_id]

    if monitor["timer"]:
        monitor["timer"].cancel()

    monitor["timer"] = threading.Timer(monitor["timeout"], fire_alert, args=[monitor_id]) 
    monitor["timer"].start()

@app.post("/monitors/<monitor_id>/pause")
def pause_monitor(monitor_id):
    if monitor_id not in monitors:
        return jsonify({"error": "Monitor not found"}), 404
    
    monitor = monitors[monitor_id]

    if monitor["timer"]:
        monitor["timer"].cancel()
        monitor["timer"] = None

    monitor["status"] = "paused"

    return jsonify({
        "message": f"Monitor {monitor_id} paused successfully",
        "monitor": {
            "id": monitor["id"],
            "timeout": monitor["timeout"],
            "alert_email": monitor["alert_email"],
            "status": monitor["status"],
            "last_heartbeat_at": monitor["last_heartbeat_at"]
        }
    }), 200

@app.delete("/monitors/<monitor_id>")
def delete_monitor(monitor_id):
    if monitor_id not in monitors:
        return jsonify({"error": "Monitor not found"}), 404
    
    monitor = monitors[monitor_id]

    if monitor["timer"]:
        monitor["timer"].cancel()

    del monitors[monitor_id]

    return jsonify({
        "message": f"Monitor {monitor_id} deleted successfully"
    }), 200

@app.get("/monitors/<monitor_id>")
def get_monitor(monitor_id):
    if monitor_id not in monitors:
        return jsonify({"error": "Monitor not found"}), 404
    
    monitor = monitors[monitor_id]

    return jsonify({
        "monitor": {
            "id": monitor["id"],
            "timeout": monitor["timeout"],
            "alert_email": monitor["alert_email"],
            "status": monitor["status"],
            "last_heartbeat_at": monitor["last_heartbeat_at"]
        }
    }), 200

@app.get("/monitors")
def list_monitors():
    return jsonify({
        "monitors": [
            {
                "id": monitor["id"],
                "timeout": monitor["timeout"],
                "alert_email": monitor["alert_email"],
                "status": monitor["status"],
                "last_heartbeat_at": monitor["last_heartbeat_at"]
            }
            for monitor in monitors.values()
        ]
    }), 200

if __name__ == "__main__":
    app.run(debug=True)