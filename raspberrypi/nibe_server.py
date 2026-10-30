import json
import os
from flask import Flask, request, jsonify
from functools import wraps
from nibe_controller import NibeController


class NibeServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.controller = NibeController()

        # Load password from config
        self.password = self._load_config()

        # Register Routes
        self._setup_routes()

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return data.get("api_password")
        except FileNotFoundError:
            print("Error: config.json not found.")
            return None

    def require_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or auth.password != self.password:
                return jsonify({"error": "Unauthorized"}), 401
            return f(*args, **kwargs)
        return decorated

    def _setup_routes(self):

        @self.app.route('/api/set', methods=['PUT', 'POST'])
        @self.app.route('/api/state', methods=['PUT', 'POST'])
        @self.require_auth
        def set_all():
            payload = request.get_json(silent=True)
            if not isinstance(payload, dict):
                return jsonify({"error": "JSON body must be an object"}), 400

            allowed = {"power", "mode", "temp", "fan", "ifeel"}
            unknown = set(payload.keys()) - allowed
            if unknown:
                return jsonify({
                    "error": f"Unsupported fields: {sorted(unknown)}. Allowed: {sorted(allowed)}"
                }), 400

            try:
                success = self.controller.set(
                    power=payload.get("power"),
                    mode=payload.get("mode"),
                    temp=payload.get("temp"),
                    fan=payload.get("fan"),
                    ifeel=payload.get("ifeel"),
                )
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400

            return jsonify({
                "status": "success" if success else "failed",
                "state": self.controller.state.copy(),
            })

        @self.app.route('/api/power/<state>', methods=['PUT'])
        @self.require_auth
        def set_power(state):
            state = state.lower()
            if state == 'on':
                success = self.controller.power_on()
            elif state == 'off':
                success = self.controller.power_off()
            else:
                return jsonify({"error": "Invalid state. Use 'on' or 'off'"}), 400

            return jsonify({"status": "success" if success else "failed", "command": f"power {state}"})

        @self.app.route('/api/temp/<int:temp>', methods=['PUT'])
        @self.require_auth
        def set_temp(temp):
            if 15 <= temp <= 30:  # Based on your previous config range
                success = self.controller.set_temperature(temp)
                return jsonify({"status": "success" if success else "failed", "temperature": temp})
            else:
                return jsonify({"error": "Temperature out of range (15-30)"}), 400

        @self.app.route('/api/fan/<mode>', methods=['PUT'])
        @self.require_auth
        def set_fan(mode):
            if mode.lower() == 'auto':
                success = self.controller.set_fan_auto()
                return jsonify({"status": "success" if success else "failed", "mode": "auto"})
            return jsonify({"error": "Invalid fan mode. Use 'auto'"}), 400

    def run(self):
        try:
            self.app.run(host=self.host, port=self.port, debug=False)
        finally:
            self.controller.close()


if __name__ == "__main__":
    server = NibeServer()
    server.run()
