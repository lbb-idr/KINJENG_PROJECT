import os
import json
import time
import subprocess
import signal
from datetime import datetime
from typing import Dict, Any, Optional

from ...utils.logger import get_logger
from ...utils.locale import set_locale
from ..zep_graph_memory_updater import ZepGraphMemoryManager
from .state import RunnerStatus, AgentAction, SimulationRunState

logger = get_logger('kinjeng.simulation_runner')

IS_WINDOWS = os.name == 'nt'


class SubprocessMixin:
    @classmethod
    def _terminate_process(cls, process, simulation_id, timeout=10):
        """Cross-platform process tree termination."""
        if IS_WINDOWS:
            logger.info(f"Terminating process tree (Windows): simulation={simulation_id}, pid={process.pid}")
            try:
                subprocess.run(
                    ['taskkill', '/PID', str(process.pid), '/T'],
                    capture_output=True, timeout=5
                )
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process unresponsive, force killing: {simulation_id}")
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(process.pid), '/T'],
                        capture_output=True, timeout=5
                    )
                    process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"taskkill failed, trying terminate: {e}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        else:
            pgid = os.getpgid(process.pid)
            logger.info(f"Terminating process group (Unix): simulation={simulation_id}, pgid={pgid}")
            os.killpg(pgid, signal.SIGTERM)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process group unresponsive to SIGTERM, force killing: {simulation_id}")
                os.killpg(pgid, signal.SIGKILL)
                process.wait(timeout=5)

    @classmethod
    def _monitor_simulation(cls, simulation_id, locale='zh'):
        """Monitor simulation process and parse action logs."""
        set_locale(locale)
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")

        process = cls._processes.get(simulation_id)
        state = cls.get_run_state(simulation_id)
        if not process or not state:
            return

        twitter_position = 0
        reddit_position = 0

        try:
            while process.poll() is None:
                if os.path.exists(twitter_actions_log):
                    twitter_position = cls._read_action_log(
                        twitter_actions_log, twitter_position, state, "twitter"
                    )
                if os.path.exists(reddit_actions_log):
                    reddit_position = cls._read_action_log(
                        reddit_actions_log, reddit_position, state, "reddit"
                    )
                cls._save_run_state(state)
                time.sleep(2)

            if os.path.exists(twitter_actions_log):
                cls._read_action_log(twitter_actions_log, twitter_position, state, "twitter")
            if os.path.exists(reddit_actions_log):
                cls._read_action_log(reddit_actions_log, reddit_position, state, "reddit")

            exit_code = process.returncode
            if exit_code == 0:
                state.runner_status = RunnerStatus.COMPLETED
                state.completed_at = datetime.now().isoformat()
                logger.info(f"Simulation completed: {simulation_id}")
            else:
                state.runner_status = RunnerStatus.FAILED
                main_log_path = os.path.join(sim_dir, "simulation.log")
                error_info = ""
                try:
                    if os.path.exists(main_log_path):
                        with open(main_log_path, 'r', encoding='utf-8') as f:
                            error_info = f.read()[-2000:]
                except Exception:
                    pass
                state.error = f"Process exit code: {exit_code}, error: {error_info}"
                logger.error(f"Simulation failed: {simulation_id}, error={state.error}")

            state.twitter_running = False
            state.reddit_running = False
            cls._save_run_state(state)

        except Exception as e:
            logger.error(f"Monitor thread exception: {simulation_id}, error={str(e)}")
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)

        finally:
            if cls._graph_memory_enabled.get(simulation_id, False):
                try:
                    ZepGraphMemoryManager.stop_updater(simulation_id)
                    logger.info(f"Stopped graph memory updater: simulation_id={simulation_id}")
                except Exception as e:
                    logger.error(f"Failed to stop graph memory updater: {e}")
                cls._graph_memory_enabled.pop(simulation_id, None)

            cls._processes.pop(simulation_id, None)
            cls._action_queues.pop(simulation_id, None)

            if simulation_id in cls._stdout_files:
                try:
                    cls._stdout_files[simulation_id].close()
                except Exception:
                    pass
                cls._stdout_files.pop(simulation_id, None)
            if simulation_id in cls._stderr_files and cls._stderr_files[simulation_id]:
                try:
                    cls._stderr_files[simulation_id].close()
                except Exception:
                    pass
                cls._stderr_files.pop(simulation_id, None)

    @classmethod
    def _read_action_log(cls, log_path, position, state, platform):
        """Read and parse action log file."""
        graph_memory_enabled = cls._graph_memory_enabled.get(state.simulation_id, False)
        graph_updater = None
        if graph_memory_enabled:
            graph_updater = ZepGraphMemoryManager.get_updater(state.simulation_id)

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(position)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        action_data = json.loads(line)

                        if "event_type" in action_data:
                            event_type = action_data.get("event_type")

                            if event_type == "simulation_end":
                                if platform == "twitter":
                                    state.twitter_completed = True
                                    state.twitter_running = False
                                elif platform == "reddit":
                                    state.reddit_completed = True
                                    state.reddit_running = False

                                all_completed = cls._check_all_platforms_completed(state)
                                if all_completed:
                                    state.runner_status = RunnerStatus.COMPLETED
                                    state.completed_at = datetime.now().isoformat()

                            elif event_type == "round_end":
                                round_num = action_data.get("round", 0)
                                simulated_hours = action_data.get("simulated_hours", 0)

                                if platform == "twitter":
                                    if round_num > state.twitter_current_round:
                                        state.twitter_current_round = round_num
                                    state.twitter_simulated_hours = simulated_hours
                                elif platform == "reddit":
                                    if round_num > state.reddit_current_round:
                                        state.reddit_current_round = round_num
                                    state.reddit_simulated_hours = simulated_hours

                                if round_num > state.current_round:
                                    state.current_round = round_num
                                state.simulated_hours = max(
                                    state.twitter_simulated_hours, state.reddit_simulated_hours
                                )
                            continue

                        action = AgentAction(
                            round_num=action_data.get("round", 0),
                            timestamp=action_data.get("timestamp", datetime.now().isoformat()),
                            platform=platform,
                            agent_id=action_data.get("agent_id", 0),
                            agent_name=action_data.get("agent_name", ""),
                            action_type=action_data.get("action_type", ""),
                            action_args=action_data.get("action_args", {}),
                            result=action_data.get("result"),
                            success=action_data.get("success", True),
                        )
                        state.add_action(action)

                        if action.round_num and action.round_num > state.current_round:
                            state.current_round = action.round_num

                        if graph_updater:
                            graph_updater.add_activity_from_dict(action_data, platform)

                    except json.JSONDecodeError:
                        pass
                return f.tell()
        except Exception as e:
            logger.warning(f"Failed to read action log: {log_path}, error={e}")
            return position

    @classmethod
    def _check_all_platforms_completed(cls, state):
        """Check whether all enabled platforms have completed."""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        twitter_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_log = os.path.join(sim_dir, "reddit", "actions.jsonl")

        twitter_enabled = os.path.exists(twitter_log)
        reddit_enabled = os.path.exists(reddit_log)

        if twitter_enabled and not state.twitter_completed:
            return False
        if reddit_enabled and not state.reddit_completed:
            return False
        return twitter_enabled or reddit_enabled
