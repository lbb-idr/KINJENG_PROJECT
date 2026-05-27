"""
OASIS Agent Profile数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class OasisAgentProfile:
    """OASIS Agent Profile数据结构"""
    # 通用字段
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str

    # 可选字段 - Reddit风格
    karma: int = 1000

    # 可选字段 - Twitter风格
    friend_count: int = 100
    follower_count: int = 150
    statuses_count: int = 500

    # 额外人设信息
    age: Optional[int] = None
    gender: Optional[str] = None
    mbti: Optional[str] = None
    country: Optional[str] = None
    profession: Optional[str] = None
    interested_topics: List[str] = field(default_factory=list)

    # Field baru untuk profil lebih realistis
    education_level: Optional[str] = None
    iq_level: Optional[str] = None
    cognitive_style: Optional[str] = None
    knowledge_level: Optional[str] = None

    # 来源实体信息
    source_entity_uuid: Optional[str] = None
    source_entity_type: Optional[str] = None

    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def to_reddit_format(self) -> Dict[str, Any]:
        """转换为Reddit平台格式"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "created_at": self.created_at,
        }

        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        if self.education_level:
            profile["education_level"] = self.education_level
        if self.iq_level:
            profile["iq_level"] = self.iq_level
        if self.cognitive_style:
            profile["cognitive_style"] = self.cognitive_style
        if self.knowledge_level:
            profile["knowledge_level"] = self.knowledge_level

        return profile

    def to_twitter_format(self) -> Dict[str, Any]:
        """转换为Twitter平台格式"""
        profile = {
            "user_id": self.user_id,
            "username": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "created_at": self.created_at,
        }

        if self.age:
            profile["age"] = self.age
        if self.gender:
            profile["gender"] = self.gender
        if self.mbti:
            profile["mbti"] = self.mbti
        if self.country:
            profile["country"] = self.country
        if self.profession:
            profile["profession"] = self.profession
        if self.interested_topics:
            profile["interested_topics"] = self.interested_topics
        if self.education_level:
            profile["education_level"] = self.education_level
        if self.iq_level:
            profile["iq_level"] = self.iq_level
        if self.cognitive_style:
            profile["cognitive_style"] = self.cognitive_style
        if self.knowledge_level:
            profile["knowledge_level"] = self.knowledge_level

        return profile

    def to_dict(self) -> Dict[str, Any]:
        """转换为完整字典格式"""
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "name": self.name,
            "bio": self.bio,
            "persona": self.persona,
            "karma": self.karma,
            "friend_count": self.friend_count,
            "follower_count": self.follower_count,
            "statuses_count": self.statuses_count,
            "age": self.age,
            "gender": self.gender,
            "mbti": self.mbti,
            "country": self.country,
            "profession": self.profession,
            "interested_topics": self.interested_topics,
            "education_level": self.education_level,
            "iq_level": self.iq_level,
            "cognitive_style": self.cognitive_style,
            "knowledge_level": self.knowledge_level,
            "source_entity_uuid": self.source_entity_uuid,
            "source_entity_type": self.source_entity_type,
            "created_at": self.created_at,
        }
