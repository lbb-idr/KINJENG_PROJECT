import os
import json
import time
import threading

from flask import jsonify, request

from . import system_bp
from ..services.simulation_runner import SimulationRunner

MODE_FILE = os.path.join(os.path.dirname(__file__), '../data/mode.json')

# --- Idle shutdown tracker ---
_last_activity = time.time()
_idle_shutdown_started = False
IDLE_TIMEOUT = 300  # 5 menit tanpa aktivitas -> shutdown


def touch():
    global _last_activity
    _last_activity = time.time()


def _idle_shutdown_loop():
    global _idle_shutdown_started
    if _idle_shutdown_started:
        return
    _idle_shutdown_started = True

    def loop():
        while True:
            time.sleep(60)
            if time.time() - _last_activity > IDLE_TIMEOUT:
                os._exit(0)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


def start_idle_shutdown():
    _idle_shutdown_loop()


# --- Routes ---

@system_bp.route('/shutdown', methods=['POST'])
def shutdown():
    SimulationRunner.cleanup_all_simulations()
    SimulationRunner._cleanup_done = False
    touch()
    return jsonify({"success": True, "message": "disconnected"})


@system_bp.route('/disconnect', methods=['POST'])
def disconnect():
    SimulationRunner.cleanup_all_simulations()
    SimulationRunner._cleanup_done = False
    touch()
    return jsonify({"success": True, "message": "disconnected"})


@system_bp.route('/graph-mode', methods=['GET'])
def get_graph_mode():
    return jsonify({'mode': _read_mode()})


@system_bp.route('/graph-mode', methods=['POST'])
def set_graph_mode():
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'local')
    if mode not in ('local', 'zep'):
        return jsonify({'success': False, 'error': 'Mode must be "local" or "zep"'}), 400
    _write_mode(mode)
    return jsonify({'success': True, 'mode': mode})


def _read_mode() -> str:
    try:
        with open(MODE_FILE, 'r') as f:
            return json.load(f).get('mode', 'local')
    except:
        return 'local'


def _write_mode(mode: str):
    os.makedirs(os.path.dirname(MODE_FILE), exist_ok=True)
    with open(MODE_FILE, 'w') as f:
        json.dump({'mode': mode}, f)
