"""
模拟相关API路由 - 包初始化
"""
from flask import Blueprint

simulation_bp = Blueprint('simulation', __name__)

# Interview prompt 优化前缀
# 添加此前缀可以避免Agent调用工具，直接用文本回复
INTERVIEW_PROMPT_PREFIX = "结合你的人设、所有的过往记忆与行动，不调用任何工具直接用文本回复我："


def optimize_interview_prompt(prompt: str) -> str:
    """
    优化Interview提问，添加前缀避免Agent调用工具
    
    Args:
        prompt: 原始提问
        
    Returns:
        优化后的提问
    """
    if not prompt:
        return prompt
    # 避免重复添加前缀
    if prompt.startswith(INTERVIEW_PROMPT_PREFIX):
        return prompt
    return f"{INTERVIEW_PROMPT_PREFIX}{prompt}"


from . import entities  # noqa: E402, F401
from . import config  # noqa: E402, F401
from . import run  # noqa: E402, F401
from . import profiles  # noqa: E402, F401
