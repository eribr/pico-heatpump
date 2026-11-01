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
            missing = allowed - set(payload.keys())
            if missing:
                return jsonify({
                    "error": f"Missing fields: {sorted(missing)}"
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

            return jsonify({"status": "success" if success else "failed"})

    def run(self):
        try:
            self.app.run(host=self.host, port=self.port, debug=False)
        finally:
            self.controller.close()


if __name__ == "__main__":
    server = NibeServer()
    server.run()
