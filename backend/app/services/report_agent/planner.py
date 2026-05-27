"""
Report Agent 大纲规划模块

包含：
- OutlinePlanner mixin: 报告大纲规划逻辑
- 规划相关的 prompt 常量
"""

import json
from typing import Dict, Any, Optional, Callable

from ...utils.locale import get_language_instruction, t
from ...utils.logger import get_logger
from .models import ReportSection, ReportOutline

logger = get_logger('mirofish.report_agent')


# ── 大纲规划 prompt ──

PLAN_SYSTEM_PROMPT = """\
你是一个「未来预测报告」的撰写专家，拥有对模拟世界的「上帝视角」——你可以洞察模拟中每一位Agent的行为、言论和互动。

【核心理念】
我们构建了一个模拟世界，并向其中注入了特定的「模拟需求」作为变量。模拟世界的演化结果，就是对未来可能发生情况的预测。你正在观察的不是"实验数据"，而是"未来的预演"。

【你的任务】
撰写一份「未来预测报告」，回答：
1. 在我们设定的条件下，未来发生了什么？
2. 各类Agent（人群）是如何反应和行动？
3. 这个模拟揭示了哪些值得关注的未来趋势和风险？

【报告定位】
- ✅ 这是一份基于模拟的未来预测报告，揭示"如果这样，未来会怎样"
- ✅ 聚焦于预测结果：事件走向、群体反应、涌现现象、潜在风险
- ✅ 模拟世界中的Agent言行就是对未来人群行为的预测
- ❌ 不是对现实世界现状的分析
- ❌ 不是泛泛而谈的舆情综述

【章节数量限制】
- 最少2个章节，最多5个章节
- 不需要子章节，每个章节直接撰写完整内容
- 内容要精炼，聚焦于核心预测发现
- 章节结构由你根据预测结果自主设计

请输出JSON格式的报告大纲，格式如下：
{
    "title": "报告标题",
    "summary": "报告摘要（一句话概括核心预测发现）",
    "sections": [
        {
            "title": "章节标题",
            "description": "章节内容描述"
        }
    ]
}

注意：sections数组最少2个，最多5个元素！"""

PLAN_USER_PROMPT_TEMPLATE = """\
{language_instruction}

【预测场景设定】
我们向模拟世界注入的变量（模拟需求）：{simulation_requirement}

【模拟世界规模】
- 参与模拟的实体数量: {total_nodes}
- 实体间产生的关系数量: {total_edges}
- 实体类型分布: {entity_types}
- 活跃Agent数量: {total_entities}

【模拟预测到的部分未来事实样本】
{related_facts_json}

请以「上帝视角」审视这个未来预演：
1. 在我们设定的条件下，未来呈现出了什么样的状态？
2. 各类人群（Agent）是如何反应和行动的？
3. 这个模拟揭示了哪些值得关注的未来趋势？

根据预测结果，设计最合适的报告章节结构。

【再次提醒】报告章节数量：最少2个，最多5个，内容要精炼聚焦于核心预测发现。"""


class OutlinePlanner:
    """Report Agent 大纲规划逻辑（mixin）"""

    def plan_outline(
        self,
        progress_callback: Optional[Callable] = None
    ) -> ReportOutline:
        """
        规划报告大纲

        使用LLM分析模拟需求，规划报告的目录结构

        Args:
            progress_callback: 进度回调函数

        Returns:
            ReportOutline: 报告大纲
        """
        logger.info(t('report.startPlanningOutline'))

        if progress_callback:
            progress_callback("planning", 0, t('progress.analyzingRequirements'))

        # 首先获取模拟上下文
        context = self.zep_tools.get_simulation_context(
            graph_id=self.graph_id,
            simulation_requirement=self.simulation_requirement
        )

        if progress_callback:
            progress_callback("planning", 30, t('progress.generatingOutline'))

        system_prompt = f"{get_language_instruction()}\n\n{PLAN_SYSTEM_PROMPT}"
        lang_instr = get_language_instruction()
        system_prompt = f"{lang_instr}\n\n{PLAN_SYSTEM_PROMPT}"
        user_prompt = PLAN_USER_PROMPT_TEMPLATE.format(
            language_instruction=lang_instr,
            simulation_requirement=self.simulation_requirement,
            total_nodes=context.get('graph_statistics', {}).get('total_nodes', 0),
            total_edges=context.get('graph_statistics', {}).get('total_edges', 0),
            entity_types=list(context.get('graph_statistics', {}).get('entity_types', {}).keys()),
            total_entities=context.get('total_entities', 0),
            related_facts_json=json.dumps(context.get('related_facts', [])[:10], ensure_ascii=False, indent=2),
        )

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )

            if progress_callback:
                progress_callback("planning", 80, t('progress.parsingOutline'))

            # 解析大纲
            sections = []
            for section_data in response.get("sections", []):
                sections.append(ReportSection(
                    title=section_data.get("title", ""),
                    content=""
                ))

            outline = ReportOutline(
                title=response.get("title", "模拟分析报告"),
                summary=response.get("summary", ""),
                sections=sections
            )

            if progress_callback:
                progress_callback("planning", 100, t('progress.outlinePlanComplete'))

            logger.info(t('report.outlinePlanDone', count=len(sections)))
            return outline

        except Exception as e:
            logger.error(t('report.outlinePlanFailed', error=str(e)))
            # 返回默认大纲（3个章节，作为fallback）
            return ReportOutline(
                title="Laporan Prediksi Simulasi",
                summary="Analisis tren masa depan dan risiko berdasarkan prediksi simulasi.",
                sections=[
                    ReportSection(title="Skenario Prediksi dan Temuan Inti"),
                    ReportSection(title="Analisis Perilaku Populasi"),
                    ReportSection(title="Prospek Tren dan Peringatan Risiko")
                ]
            )
