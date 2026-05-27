import os
import sys
import signal
import atexit
import time
import threading
from typing import Dict, Optional

from ...utils.logger import get_logger

logger = get_logger('mirofish.simulation_runner')

_cleanup_registered = False


class HeartbeatMixin:
    _last_heartbeat: Dict[str, float] = {}
    _cleanup_thread: Optional[threading.Thread] = None
    _stop_cleanup = False

    @classmethod
    def start_cleanup_thread(cls):
        """Start background thread to stop stale simulations (no heartbeat >5min)."""
        if cls._cleanup_thread and cls._cleanup_thread.is_alive():
            return
        cls._stop_cleanup = False
        cls._cleanup_thread = threading.Thread(
            target=cls._cleanup_loop, daemon=True, name='heartbeat-cleanup'
        )
        cls._cleanup_thread.start()
        logger.info("Heartbeat cleanup thread started")

    @classmethod
    def stop_cleanup_thread(cls):
        cls._stop_cleanup = True

    @classmethod
    def _cleanup_loop(cls):
        while not cls._stop_cleanup:
            try:
                now = time.time()
                stale = [
                    sim_id for sim_id, ts in list(cls._last_heartbeat.items())
                    if now - ts > 300
                ]
                for sim_id in stale:
                    logger.warning(f"Auto-stopping stale simulation (no heartbeat): {sim_id}")
                    try:
                        cls.stop_simulation(sim_id)
                    except Exception as e:
                        logger.error(f"Failed to auto-stop stale simulation {sim_id}: {e}")
                    finally:
                        cls._last_heartbeat.pop(sim_id, None)
                        cls._run_states.pop(sim_id, None)
                        cls._processes.pop(sim_id, None)
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
            time.sleep(60)

    @classmethod
    def register_cleanup(cls):
        """Register cleanup handlers for Flask shutdown."""
        global _cleanup_registered

        if _cleanup_registered:
            return

        is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        is_debug_mode = os.environ.get('FLASK_DEBUG') == '1' or os.environ.get('WERKZEUG_RUN_MAIN') is not None

        if is_debug_mode and not is_reloader_process:
            _cleanup_registered = True
            return

        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        original_sighup = None
        has_sighup = hasattr(signal, 'SIGHUP')
        if has_sighup:
            original_sighup = signal.getsignal(signal.SIGHUP)

        def cleanup_handler(signum=None, frame=None):
            if cls._processes or cls._graph_memory_enabled:
                logger.info(f"Received signal {signum}, cleaning up...")
            cls.cleanup_all_simulations()
            if signum == signal.SIGINT and callable(original_sigint):
                original_sigint(signum, frame)
            elif signum == signal.SIGTERM and callable(original_sigterm):
                original_sigterm(signum, frame)
            elif has_sighup and signum == signal.SIGHUP:
                if callable(original_sighup):
                    original_sighup(signum, frame)
                else:
                    sys.exit(0)
            else:
                raise KeyboardInterrupt

        atexit.register(cls.cleanup_all_simulations)

        try:
            signal.signal(signal.SIGTERM, cleanup_handler)
            signal.signal(signal.SIGINT, cleanup_handler)
            if has_sighup:
                signal.signal(signal.SIGHUP, cleanup_handler)
        except ValueError:
            logger.warning("Cannot register signal handlers (not in main thread), using atexit only")

        _cleanup_registered = True
