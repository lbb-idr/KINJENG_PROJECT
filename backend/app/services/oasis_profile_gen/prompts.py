"""
Prompt templates and system prompts for OASIS profile generation
"""

import json
from typing import Dict, Any

from ...utils.locale import get_language_instruction

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

COUNTRIES = [
    "China", "US", "UK", "Japan", "Germany", "France",
    "Canada", "Australia", "Brazil", "India", "South Korea"
]

INDIVIDUAL_ENTITY_TYPES = [
    "student", "alumni", "professor", "person", "publicfigure",
    "expert", "faculty", "official", "journalist", "activist"
]

GROUP_ENTITY_TYPES = [
    "university", "governmentagency", "organization", "ngo",
    "mediaoutlet", "company", "institution", "group", "community"
]


def get_sim_type_prompt_context(sim_type: str) -> str:
    """Dapatkan konteks tambahan berdasarkan tipe simulasi untuk prompt profil"""
    contexts = {
        "academic": "Konteks simulasi akademik: Fokus pada riset, publikasi, dan diskusi ilmiah. Profile agen harus mencerminkan latar belakang akademik: gelar, afiliasi universitas/riset, minat penelitian, publikasi, dan pengalaman mengajar/riset.",
        "political": "Konteks simulasi politik: Fokus pada opini publik dan dinamika politik. Profile agen harus mencerminkan afiliasi politik: preferensi partai, ideologi, aktivisme politik, pengalaman organisasi politik/kampanye, dan isu-isu sosial yang diperjuangkan.",
        "market": "Konteks simulasi pasar: Fokus pada perilaku konsumen dan tren bisnis. Profile agen harus mencerminkan peran ekonomi: profesi, kebiasaan konsumsi, preferensi merek, perilaku belanja, dan pengaruh sebagai konsumen.",
        "social": "Konteks simulasi sosial: Fokus pada interaksi sosial dan isu kemasyarakatan. Profile agen harus mencerminkan latar belakang sosial yang beragam: komunitas, hobi, kegiatan sosial, jaringan pertemanan, dan peran dalam masyarakat.",
        "custom": "Konteks simulasi kustom: Profile agen mengikuti kebutuhan spesifik pengguna seperti yang didefinisikan dalam kebutuhan simulasi."
    }
    return contexts.get(sim_type, "")


def get_system_prompt(is_individual: bool, sim_type: str = "academic") -> str:
    """获取系统提示词"""
    base_prompt = "你是社交媒体用户画像生成专家。生成详细、真实的人设用于舆论模拟,最大程度还原已有现实情况。必须返回有效的JSON格式，所有字符串值不能包含未转义的换行符。"
    sim_type_info = get_sim_type_prompt_context(sim_type)
    if sim_type_info:
        base_prompt = f"{base_prompt}\n\n{sim_type_info}"
    return f"{base_prompt}\n\n{get_language_instruction()}"


def build_individual_persona_prompt(
    entity_name: str,
    entity_type: str,
    entity_summary: str,
    entity_attributes: Dict[str, Any],
    context: str,
    sim_type_context: str = ""
) -> str:
    """构建个人实体的详细人设提示词"""
    attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "无"
    context_str = context[:3000] if context else "无额外上下文"
    sim_type_info = f"\n\n### Konteks Tipe Simulasi\n{sim_type_context}" if sim_type_context else ""

    return f"""{sim_type_info}
为实体生成详细的社交媒体用户人设,最大程度还原已有现实情况。

实体名称: {entity_name}
实体类型: {entity_type}
实体摘要: {entity_summary}
实体属性: {attrs_str}

上下文信息:
{context_str}

请生成JSON，包含以下字段:

1. bio: 社交媒体简介，200字
2. persona: 详细人设描述（2000字的纯文本），需包含:
   - 基本信息（年龄、职业、教育背景、所在地）
   - 人物背景（重要经历、与事件的关联、社会关系）
   - 性格特征（MBTI类型、核心性格、情绪表达方式）
   - 社交媒体行为（发帖频率、内容偏好、互动风格、语言特点）
   - 立场观点（对话题的态度、可能被激怒/感动的内容）
   - 争议性观点（这个人物在公共议题上最可能引发争议的立场）
   - 情绪触发点（什么内容最容易让这个人情绪化回应）
   - 辩论风格（理性论证、感性诉诸、讽刺挖苦、数据驱动等）
   - 独特特征（口头禅、特殊经历、个人爱好）
   - 个人记忆（人设的重要部分，要介绍这个个体与事件的关联，以及这个个体在事件中的已有动作与反应）
3. age: 年龄数字（必须是整数）
4. gender: 性别，必须是英文: "male" 或 "female"
5. mbti: MBTI类型（如INTJ、ENFP等）
6. country: 国家（使用中文，如"中国"）
7. profession: 职业
8. interested_topics: 感兴趣话题数组
9. education_level: 教育程度，如"SD/SMP", "SMA/SMK", "D3", "S1", "S2/S3"
10. iq_level: 智力水平，如"Sangat Rendah", "Rendah", "Rata-rata", "Tinggi", "Sangat Tinggi"
11. cognitive_style: 认知风格，如"Analitis", "Intuitif", "Praktis", "Kreatif", "Logis", "Emosional"
12. knowledge_level: 对模拟主题的知识水平，如"Rendah", "Sedang", "Tinggi", "Ahli"

重要:
- 所有字段值必须是字符串或数字，不要使用换行符
- persona必须是一段连贯的文字描述
- {get_language_instruction()} (gender字段必须用英文male/female)
- 内容要与实体信息保持一致
- age必须是有效的整数，gender必须是"male"或"female"
"""


def build_group_persona_prompt(
    entity_name: str,
    entity_type: str,
    entity_summary: str,
    entity_attributes: Dict[str, Any],
    context: str,
    sim_type_context: str = ""
) -> str:
    """构建群体/机构实体的详细人设提示词"""
    attrs_str = json.dumps(entity_attributes, ensure_ascii=False) if entity_attributes else "无"
    context_str = context[:3000] if context else "无额外上下文"
    sim_type_info = f"\n\n### Konteks Tipe Simulasi\n{sim_type_context}" if sim_type_context else ""

    return f"""{sim_type_info}
为机构/群体实体生成详细的社交媒体账号设定,最大程度还原已有现实情况。

实体名称: {entity_name}
实体类型: {entity_type}
实体摘要: {entity_summary}
实体属性: {attrs_str}

上下文信息:
{context_str}

请生成JSON，包含以下字段:

1. bio: 官方账号简介，200字，专业得体
2. persona: 详细账号设定描述（2000字的纯文本），需包含:
   - 机构基本信息（正式名称、机构性质、成立背景、主要职能）
   - 账号定位（账号类型、目标受众、核心功能）
   - 发言风格（语言特点、常用表达、禁忌话题）
   - 发布内容特点（内容类型、发布频率、活跃时间段）
   - 立场态度（对核心话题的官方立场、面对争议的处理方式）
   - 特殊说明（代表的群体画像、运营习惯）
   - 机构记忆（机构人设的重要部分，要介绍这个机构与事件的关联，以及这个机构在事件中的已有动作与反应）
3. age: 固定填30（机构账号的虚拟年龄）
4. gender: 固定填"other"（机构账号使用other表示非个人）
5. mbti: MBTI类型，用于描述账号风格，如ISTJ代表严谨保守
6. country: 国家（使用中文，如"中国"）
7. profession: 机构职能描述
8. interested_topics: 关注领域数组
9. education_level: 机构类型，如"Lembaga Riset", "Pemerintahan", "Media", "Pendidikan"
10. iq_level: 固定填"Rata-rata"（机构账号的智力水平）
11. cognitive_style: 机构风格，如"Formal", "Informatif", "Netral", "Otoritatif"
12. knowledge_level: 机构专业水平，如"Ahli"

重要:
- 所有字段值必须是字符串或数字，不允许null值
- persona必须是一段连贯的文字描述，不要使用换行符
- {get_language_instruction()} (gender字段必须用英文"other")
- age必须是整数30，gender必须是字符串"other"
- 机构账号发言要符合其身份定位"""
