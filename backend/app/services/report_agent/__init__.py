"""
Report Agent服务

使用LangChain + Zep实现ReACT模式的模拟报告生成

功能：
1. 根据模拟需求和Zep图谱信息生成报告
2. 先规划目录结构，然后分段生成
3. 每段采用ReACT多轮思考与反思模式
4. 支持与用户对话，在对话中自主调用检索工具
"""

from typing import Dict, Any, Optional

from ...utils.llm_client import LLMClient
from ...utils.logger import get_logger
from ...utils.locale import t
from ..zep_tools import ZepToolsService

from .logger import ReportLogger, ReportConsoleLogger
from .planner import OutlinePlanner
from .generator import SectionGenerator, ReportManager
from .tools import ReportTools
from .models import ReportStatus, ReportSection, ReportOutline, Report

logger = get_logger('mirofish.report_agent')


class ReportAgent(OutlinePlanner, SectionGenerator, ReportTools):
    """
    Report Agent - 模拟报告生成Agent

    采用ReACT（Reasoning + Acting）模式：
    1. 规划阶段：分析模拟需求，规划报告目录结构
    2. 生成阶段：逐章节生成内容，每章节可多次调用工具获取信息
    3. 反思阶段：检查内容完整性和准确性
    """

    # 最大工具调用次数（每个章节）
    MAX_TOOL_CALLS_PER_SECTION = 5

    # 最大反思轮数
    MAX_REFLECTION_ROUNDS = 3

    # 对话中的最大工具调用次数
    MAX_TOOL_CALLS_PER_CHAT = 2

    def __init__(
        self,
        graph_id: str,
        simulation_id: str,
        simulation_requirement: str,
        llm_client: Optional[LLMClient] = None,
        zep_tools: Optional[ZepToolsService] = None
    ):
        """
        初始化Report Agent

        Args:
            graph_id: 图谱ID
            simulation_id: 模拟ID
            simulation_requirement: 模拟需求描述
            llm_client: LLM客户端（可选）
            zep_tools: Zep工具服务（可选）
        """
        self.graph_id = graph_id
        self.simulation_id = simulation_id
        self.simulation_requirement = simulation_requirement

        self.llm = llm_client or LLMClient()
        self.zep_tools = zep_tools or ZepToolsService()

        # 工具定义
        self.tools = self._define_tools()

        # 日志记录器（在 generate_report 中初始化）
        self.report_logger: Optional[ReportLogger] = None
        # 控制台日志记录器（在 generate_report 中初始化）
        self.console_logger: Optional[ReportConsoleLogger] = None

        logger.info(t('report.agentInitDone', graphId=graph_id, simulationId=simulation_id))
