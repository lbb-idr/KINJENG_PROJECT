"""
API路由模块
"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
survey_bp = Blueprint('survey', __name__)
cognitive_bp = Blueprint('cognitive', __name__)
system_bp = Blueprint('system', __name__)

from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401
from . import survey  # noqa: E402, F401
from . import survey_engine  # noqa: E402, F401
from . import report_pdf  # noqa: E402, F401
from . import cognitive  # noqa: E402, F401
from . import system  # noqa: E402, F401

