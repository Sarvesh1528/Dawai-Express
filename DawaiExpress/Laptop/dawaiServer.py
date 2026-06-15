import threading
from flask import Flask, jsonify, request
from flask_cors import CORS

from database import get_pats

app = Flask(__name__)
CORS(app)

qt_bridge = None  # Will be set by PyQt

@app.get('/ping')
def ping():
    return jsonify({"status": "Server is alive!"})

@app.post('/xpress')
def update():
    data = request.get_json()
    print("xpress:", data)
    if qt_bridge:
        qt_bridge({"xpress": data["xpress"]})
    return jsonify({"status": "success"})

@app.post("/alerts")
def alerts():
    data = request.get_json()
    print("alert:", data["alert"])
    if qt_bridge:
        qt_bridge({"alert": data["alert"]})
    return jsonify({"status": "success"})

@app.post("/status")
def status():
    data = request.get_json()
    print("Status:", data)
    if qt_bridge:
        qt_bridge({"status": data})
    return jsonify({"status": "success"})

@app.post("/patlist")
def pats():
    data = request.get_json()
    print("Status:", data)
    if qt_bridge:
        pass
        # qt_bridge({"status": data})
    patList = get_pats()
    patDict = {}
    for i,j in enumerate(patList):
        print(i, j)
        patDict[i] = j
    # print(patDict)
    return jsonify(patDict)

def connect_pyqt_bridge(callback):
    """Link Flask app to PyQt signal emitter"""
    global qt_bridge
    qt_bridge = callback

def startServer():
    try:
        def run_server():
            app.run(host="0.0.0.0", port=8081, debug=False, use_reloader=False)

        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        print("Flask server thread started on port 8081")
        return True
    except Exception as e:
        print("Error starting server:", e)
        return False
