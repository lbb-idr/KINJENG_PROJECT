"""
Helper functions for OASIS profile generation
"""

import json
import random
import re
from typing import Dict, Any, Optional, List

from .models import OasisAgentProfile
from .prompts import MBTI_TYPES, COUNTRIES, INDIVIDUAL_ENTITY_TYPES, GROUP_ENTITY_TYPES
from ...utils.locale import t


def generate_username(name: str) -> str:
    """生成用户名"""
    username = name.lower().replace(" ", "_")
    username = ''.join(c for c in username if c.isalnum() or c == '_')
    suffix = random.randint(100, 999)
    return f"{username}_{suffix}"


def fix_truncated_json(content: str) -> str:
    """修复被截断的JSON（输出被max_tokens限制截断）"""
    content = content.strip()

    open_braces = content.count('{') - content.count('}')
    open_brackets = content.count('[') - content.count(']')

    if content and content[-1] not in '",}]':
        content += '"'

    content += ']' * open_brackets
    content += '}' * open_braces

    return content


def try_fix_json(content: str, entity_name: str, entity_type: str, entity_summary: str = "") -> Dict[str, Any]:
    """尝试修复损坏的JSON"""
    content = fix_truncated_json(content)

    json_match = re.search(r'\{[\s\S]*\}', content)
    if json_match:
        json_str = json_match.group()

        def fix_string_newlines(match):
            s = match.group(0)
            s = s.replace('\n', ' ').replace('\r', ' ')
            s = re.sub(r'\s+', ' ', s)
            return s

        json_str = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', fix_string_newlines, json_str)

        try:
            result = json.loads(json_str)
            result["_fixed"] = True
            return result
        except json.JSONDecodeError:
            try:
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
                json_str = re.sub(r'\s+', ' ', json_str)
                result = json.loads(json_str)
                result["_fixed"] = True
                return result
            except:
                pass

    bio_match = re.search(r'"bio"\s*:\s*"([^"]*)"', content)
    persona_match = re.search(r'"persona"\s*:\s*"([^"]*)', content)

    bio = bio_match.group(1) if bio_match else (entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}")
    persona = persona_match.group(1) if persona_match else (entity_summary or f"{entity_name}是一个{entity_type}。")

    if bio_match or persona_match:
        return {
            "bio": bio,
            "persona": persona,
            "_fixed": True
        }

    return {
        "bio": entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}",
        "persona": entity_summary or f"{entity_name}是一个{entity_type}。"
    }


def normalize_gender(gender: Optional[str]) -> str:
    """标准化gender字段为OASIS要求的英文格式"""
    if not gender:
        return "other"

    gender_lower = gender.lower().strip()

    gender_map = {
        "男": "male",
        "女": "female",
        "机构": "other",
        "其他": "other",
        "male": "male",
        "female": "female",
        "other": "other",
    }

    return gender_map.get(gender_lower, "other")


def generate_profile_rule_based(
    entity_name: str,
    entity_type: str,
    entity_summary: str,
    entity_attributes: Dict[str, Any]
) -> Dict[str, Any]:
    """使用规则生成基础人设"""
    entity_type_lower = entity_type.lower()

    if entity_type_lower in ["student", "alumni"]:
        return {
            "bio": f"{entity_type} with interests in academics and social issues.",
            "persona": f"{entity_name} is a {entity_type.lower()} who is actively engaged in academic and social discussions. They enjoy sharing perspectives and connecting with peers.",
            "age": random.randint(18, 30),
            "gender": random.choice(["male", "female"]),
            "mbti": random.choice(MBTI_TYPES),
            "country": random.choice(COUNTRIES),
            "profession": "Student",
            "interested_topics": ["Education", "Social Issues", "Technology"],
            "education_level": random.choice(["SMA/SMK", "D3", "S1"]),
            "iq_level": random.choice(["Rata-rata", "Tinggi"]),
            "cognitive_style": random.choice(["Analitis", "Kreatif", "Intuitif", "Praktis"]),
            "knowledge_level": "Sedang",
        }

    elif entity_type_lower in ["publicfigure", "expert", "faculty"]:
        return {
            "bio": f"Expert and thought leader in their field.",
            "persona": f"{entity_name} is a recognized {entity_type.lower()} who shares insights and opinions on important matters. They are known for their expertise and influence in public discourse.",
            "age": random.randint(35, 60),
            "gender": random.choice(["male", "female"]),
            "mbti": random.choice(["ENTJ", "INTJ", "ENTP", "INTP"]),
            "country": random.choice(COUNTRIES),
            "profession": entity_attributes.get("occupation", "Expert"),
            "interested_topics": ["Politics", "Economics", "Culture & Society"],
            "education_level": "S2/S3",
            "iq_level": random.choice(["Tinggi", "Sangat Tinggi"]),
            "cognitive_style": random.choice(["Analitis", "Logis", "Praktis"]),
            "knowledge_level": "Ahli",
        }

    elif entity_type_lower in ["mediaoutlet", "socialmediaplatform"]:
        return {
            "bio": f"Official account for {entity_name}. News and updates.",
            "persona": f"{entity_name} is a media entity that reports news and facilitates public discourse. The account shares timely updates and engages with the audience on current events.",
            "age": 30,
            "gender": "other",
            "mbti": "ISTJ",
            "country": "中国",
            "profession": "Media",
            "interested_topics": ["General News", "Current Events", "Public Affairs"],
            "education_level": "Lembaga Media",
            "iq_level": "Rata-rata",
            "cognitive_style": "Informatif",
            "knowledge_level": "Ahli",
        }

    elif entity_type_lower in ["university", "governmentagency", "ngo", "organization"]:
        return {
            "bio": f"Official account of {entity_name}.",
            "persona": f"{entity_name} is an institutional entity that communicates official positions, announcements, and engages with stakeholders on relevant matters.",
            "age": 30,
            "gender": "other",
            "mbti": "ISTJ",
            "country": "中国",
            "profession": entity_type,
            "interested_topics": ["Public Policy", "Community", "Official Announcements"],
            "education_level": "Lembaga",
            "iq_level": "Rata-rata",
            "cognitive_style": random.choice(["Formal", "Netral", "Otoritatif"]),
            "knowledge_level": "Ahli",
        }

    else:
        return {
            "bio": entity_summary[:150] if entity_summary else f"{entity_type}: {entity_name}",
            "persona": entity_summary or f"{entity_name} is a {entity_type.lower()} participating in social discussions.",
            "age": random.randint(25, 50),
            "gender": random.choice(["male", "female"]),
            "mbti": random.choice(MBTI_TYPES),
            "country": random.choice(COUNTRIES),
            "profession": entity_type,
            "interested_topics": ["General", "Social Issues"],
            "education_level": random.choice(["SD/SMP", "SMA/SMK", "D3", "S1"]),
            "iq_level": random.choice(["Rendah", "Rata-rata", "Tinggi"]),
            "cognitive_style": random.choice(["Analitis", "Intuitif", "Praktis", "Kreatif", "Logis", "Emosional"]),
            "knowledge_level": random.choice(["Rendah", "Sedang", "Tinggi"]),
        }


def print_generated_profile(entity_name: str, entity_type: str, profile: OasisAgentProfile):
    """实时输出生成的人设到控制台（完整内容，不截断）"""
    separator = "-" * 70

    topics_str = ', '.join(profile.interested_topics) if profile.interested_topics else '无'

    output_lines = [
        f"\n{separator}",
        t('progress.profileGenerated', name=entity_name, type=entity_type),
        f"{separator}",
        f"用户名: {profile.user_name}",
        f"",
        f"【简介】",
        f"{profile.bio}",
        f"",
        f"【详细人设】",
        f"{profile.persona}",
        f"",
        f"【基本属性】",
        f"年龄: {profile.age} | 性别: {profile.gender} | MBTI: {profile.mbti}",
        f"职业: {profile.profession} | 国家: {profile.country}",
        f"教育: {profile.education_level} | IQ: {profile.iq_level} | Kognitif: {profile.cognitive_style} | Pengetahuan: {profile.knowledge_level}",
        f"兴趣话题: {topics_str}",
        separator
    ]

    output = "\n".join(output_lines)
    print(output)
