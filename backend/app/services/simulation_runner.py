"""
Backward-compat: re-exports from the sim_runner package.
Usage: from ..services.simulation_runner import SimulationRunner
"""
from .sim_runner import SimulationRunner
from .sim_runner.state import RunnerStatus, AgentAction, RoundSummary, SimulationRunState
