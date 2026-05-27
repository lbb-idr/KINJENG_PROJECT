"""
OASIS Agent Profile Generator

将Zep图谱中的实体转换为OASIS模拟平台所需的Agent Profile格式
"""

import json
import random
import time
from typing import Dict, Any, List, Optional
import concurrent.futures
from threading import Lock

from ...config import Config
from ...utils.llm_client import LLMClient
from ...utils.logger import get_logger
from ...utils.locale import get_language_instruction, get_locale, set_locale, t
from ..zep_entity_reader import EntityNode, ZepEntityReader
from .models import OasisAgentProfile
from .prompts import (
    MBTI_TYPES, COUNTRIES, INDIVIDUAL_ENTITY_TYPES, GROUP_ENTITY_TYPES,
    get_sim_type_prompt_context, get_system_prompt,
    build_individual_persona_prompt, build_group_persona_prompt
)
from .utils import (
    generate_username, try_fix_json, normalize_gender,
    generate_profile_rule_based, print_generated_profile
)

logger = get_logger('mirofish.oasis_profile')


class OasisProfileGenerator:
    """
    OASIS Profile生成器

    将Zep图谱中的实体转换为OASIS模拟所需的Agent Profile

    优化特性：
    1. 调用Zep图谱检索功能获取更丰富的上下文
    2. 生成非常详细的人设（包括基本信息、职业经历、性格特征、社交媒体行为等）
    3. 区分个人实体和抽象群体实体
    """

    MBTI_TYPES = MBTI_TYPES
    COUNTRIES = COUNTRIES
    INDIVIDUAL_ENTITY_TYPES = INDIVIDUAL_ENTITY_TYPES
    GROUP_ENTITY_TYPES = GROUP_ENTITY_TYPES

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        zep_api_key: Optional[str] = None,
        graph_id: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model_name = model_name or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.llm = LLMClient(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model_name
        )

        self.zep_api_key = zep_api_key or Config.ZEP_API_KEY
        self.zep_client = None
        self.graph_id = graph_id

        if self.zep_api_key:
            try:
                from zep_python import Zep
                self.zep_client = Zep(api_key=self.zep_api_key)
            except Exception as e:
                logger.warning(f"Zep客户端初始化失败: {e}")

    def _is_individual_entity(self, entity_type: str) -> bool:
        """判断是否是个人类型实体"""
        return entity_type.lower() in self.INDIVIDUAL_ENTITY_TYPES

    def _is_group_entity(self, entity_type: str) -> bool:
        """判断是否是群体/机构类型实体"""
        return entity_type.lower() in self.GROUP_ENTITY_TYPES

    def set_graph_id(self, graph_id: str):
        """设置图谱ID用于Zep检索"""
        self.graph_id = graph_id

    def generate_profile_from_entity(
        self,
        entity: EntityNode,
        user_id: int,
        use_llm: bool = True,
        sim_type: str = "academic"
    ) -> OasisAgentProfile:
        """
        从Zep实体生成OASIS Agent Profile
        """
        entity_type = entity.get_entity_type() or "Entity"

        name = entity.name
        user_name = generate_username(name)

        context = self._build_entity_context(entity)

        if use_llm:
            profile_data = self._generate_profile_with_llm(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes,
                context=context,
                sim_type=sim_type
            )
        else:
            profile_data = generate_profile_rule_based(
                entity_name=name,
                entity_type=entity_type,
                entity_summary=entity.summary,
                entity_attributes=entity.attributes
            )

        return OasisAgentProfile(
            user_id=user_id,
            user_name=user_name,
            name=name,
            bio=profile_data.get("bio", f"{entity_type}: {name}"),
            persona=profile_data.get("persona", entity.summary or f"A {entity_type} named {name}."),
            karma=profile_data.get("karma", random.randint(500, 5000)),
            friend_count=profile_data.get("friend_count", random.randint(50, 500)),
            follower_count=profile_data.get("follower_count", random.randint(100, 1000)),
            statuses_count=profile_data.get("statuses_count", random.randint(100, 2000)),
            age=profile_data.get("age"),
            gender=profile_data.get("gender"),
            mbti=profile_data.get("mbti"),
            country=profile_data.get("country"),
            profession=profile_data.get("profession"),
            interested_topics=profile_data.get("interested_topics", []),
            education_level=profile_data.get("education_level"),
            iq_level=profile_data.get("iq_level"),
            cognitive_style=profile_data.get("cognitive_style"),
            knowledge_level=profile_data.get("knowledge_level"),
            source_entity_uuid=entity.uuid,
            source_entity_type=entity_type,
        )

    def _search_zep_for_entity(self, entity: EntityNode) -> Dict[str, Any]:
        """
        使用Zep图谱混合搜索功能获取实体相关的丰富信息
        """
        if not self.zep_client:
            return {"facts": [], "node_summaries": [], "context": ""}

        entity_name = entity.name

        results = {
            "facts": [],
            "node_summaries": [],
            "context": ""
        }

        if not self.graph_id:
            logger.debug(f"跳过Zep检索：未设置graph_id")
            return results

        comprehensive_query = t('progress.zepSearchQuery', name=entity_name)

        def search_edges():
            """搜索边（事实/关系）- 带重试机制"""
            max_retries = 3
            last_exception = None
            delay = 2.0

            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=30,
                        scope="edges",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep边搜索第 {attempt + 1} 次失败: {str(e)[:80]}, 重试中...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep边搜索在 {max_retries} 次尝试后仍失败: {e}")
            return None

        def search_nodes():
            """搜索节点（实体摘要）- 带重试机制"""
            max_retries = 3
            last_exception = None
            delay = 2.0

            for attempt in range(max_retries):
                try:
                    return self.zep_client.graph.search(
                        query=comprehensive_query,
                        graph_id=self.graph_id,
                        limit=20,
                        scope="nodes",
                        reranker="rrf"
                    )
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.debug(f"Zep节点搜索第 {attempt + 1} 次失败: {str(e)[:80]}, 重试中...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        logger.debug(f"Zep节点搜索在 {max_retries} 次尝试后仍失败: {e}")
            return None

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                edge_future = executor.submit(search_edges)
                node_future = executor.submit(search_nodes)

                edge_result = edge_future.result(timeout=30)
                node_result = node_future.result(timeout=30)

            all_facts = set()
            if edge_result and hasattr(edge_result, 'edges') and edge_result.edges:
                for edge in edge_result.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        all_facts.add(edge.fact)
            results["facts"] = list(all_facts)

            all_summaries = set()
            if node_result and hasattr(node_result, 'nodes') and node_result.nodes:
                for node in node_result.nodes:
                    if hasattr(node, 'summary') and node.summary:
                        all_summaries.add(node.summary)
                    if hasattr(node, 'name') and node.name and node.name != entity_name:
                        all_summaries.add(f"相关实体: {node.name}")
            results["node_summaries"] = list(all_summaries)

            context_parts = []
            if results["facts"]:
                context_parts.append("事实信息:\n" + "\n".join(f"- {f}" for f in results["facts"][:20]))
            if results["node_summaries"]:
                context_parts.append("相关实体:\n" + "\n".join(f"- {s}" for s in results["node_summaries"][:10]))
            results["context"] = "\n\n".join(context_parts)

            logger.info(f"Zep混合检索完成: {entity_name}, 获取 {len(results['facts'])} 条事实, {len(results['node_summaries'])} 个相关节点")

        except concurrent.futures.TimeoutError:
            logger.warning(f"Zep检索超时 ({entity_name})")
        except Exception as e:
            logger.warning(f"Zep检索失败 ({entity_name}): {e}")

        return results

    def _build_entity_context(self, entity: EntityNode) -> str:
        """
        构建实体的完整上下文信息
        """
        context_parts = []

        if entity.attributes:
            attrs = []
            for key, value in entity.attributes.items():
                if value and str(value).strip():
                    attrs.append(f"- {key}: {value}")
            if attrs:
                context_parts.append("### 实体属性\n" + "\n".join(attrs))

        existing_facts = set()
        if entity.related_edges:
            relationships = []
            for edge in entity.related_edges:
                fact = edge.get("fact", "")
                edge_name = edge.get("edge_name", "")
                direction = edge.get("direction", "")

                if fact:
                    relationships.append(f"- {fact}")
                    existing_facts.add(fact)
                elif edge_name:
                    if direction == "outgoing":
                        relationships.append(f"- {entity.name} --[{edge_name}]--> (相关实体)")
                    else:
                        relationships.append(f"- (相关实体) --[{edge_name}]--> {entity.name}")

            if relationships:
                context_parts.append("### 相关事实和关系\n" + "\n".join(relationships))

        if entity.related_nodes:
            related_info = []
            for node in entity.related_nodes:
                node_name = node.get("name", "")
                node_labels = node.get("labels", [])
                node_summary = node.get("summary", "")

                custom_labels = [l for l in node_labels if l not in ["Entity", "Node"]]
                label_str = f" ({', '.join(custom_labels)})" if custom_labels else ""

                if node_summary:
                    related_info.append(f"- **{node_name}**{label_str}: {node_summary}")
                else:
                    related_info.append(f"- **{node_name}**{label_str}")

            if related_info:
                context_parts.append("### 关联实体信息\n" + "\n".join(related_info))

        zep_results = self._search_zep_for_entity(entity)

        if zep_results.get("facts"):
            new_facts = [f for f in zep_results["facts"] if f not in existing_facts]
            if new_facts:
                context_parts.append("### Zep检索到的事实信息\n" + "\n".join(f"- {f}" for f in new_facts[:15]))

        if zep_results.get("node_summaries"):
            context_parts.append("### Zep检索到的相关节点\n" + "\n".join(f"- {s}" for s in zep_results["node_summaries"][:10]))

        return "\n\n".join(context_parts)

    def _generate_profile_with_llm(
        self,
        entity_name: str,
        entity_type: str,
        entity_summary: str,
        entity_attributes: Dict[str, Any],
        context: str,
        sim_type: str = "academic"
    ) -> Dict[str, Any]:
        """
        使用LLM生成非常详细的人设
        """
        is_individual = self._is_individual_entity(entity_type)

        sim_type_context = get_sim_type_prompt_context(sim_type)

        if is_individual:
            prompt = build_individual_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context,
                sim_type_context=sim_type_context
            )
        else:
            prompt = build_group_persona_prompt(
                entity_name, entity_type, entity_summary, entity_attributes, context,
                sim_type_context=sim_type_context
            )

        max_attempts = 3
        last_error = None

        for attempt in range(max_attempts):
            try:
                content = self.llm.chat(
                    messages=[
                        {"role": "system", "content": get_system_prompt(is_individual, sim_type)},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7 - (attempt * 0.1)
                )

                try:
                    result = json.loads(content)

                    if "bio" not in result or not result["bio"]:
                        result["bio"] = entity_summary[:200] if entity_summary else f"{entity_type}: {entity_name}"
                    if "persona" not in result or not result["persona"]:
                        result["persona"] = entity_summary or f"{entity_name}是一个{entity_type}。"

                    return result

                except json.JSONDecodeError as je:
                    logger.warning(f"JSON解析失败 (attempt {attempt+1}): {str(je)[:80]}")

                    result = try_fix_json(content, entity_name, entity_type, entity_summary)
                    if result.get("_fixed"):
                        del result["_fixed"]
                        return result

                    last_error = je

            except Exception as e:
                logger.warning(f"LLM调用失败 (attempt {attempt+1}): {str(e)[:80]}")
                last_error = e
                time.sleep(1 * (attempt + 1))

        logger.warning(f"LLM生成人设失败（{max_attempts}次尝试）: {last_error}, 使用规则生成")
        return generate_profile_rule_based(
            entity_name, entity_type, entity_summary, entity_attributes
        )

    def generate_profiles_from_entities(
        self,
        entities: List[EntityNode],
        use_llm: bool = True,
        progress_callback: Optional[callable] = None,
        graph_id: Optional[str] = None,
        parallel_count: int = 5,
        realtime_output_path: Optional[str] = None,
        output_platform: str = "reddit",
        sim_type: str = "academic"
    ) -> List[OasisAgentProfile]:
        """
        批量从实体生成Agent Profile（支持并行生成）
        """
        if graph_id:
            self.graph_id = graph_id

        total = len(entities)
        profiles = [None] * total
        completed_count = [0]
        lock = Lock()

        def save_profiles_realtime():
            """实时保存已生成的 profiles 到文件"""
            if not realtime_output_path:
                return

            with lock:
                existing_profiles = [p for p in profiles if p is not None]
                if not existing_profiles:
                    return

                try:
                    if output_platform == "reddit":
                        profiles_data = [p.to_reddit_format() for p in existing_profiles]
                        with open(realtime_output_path, 'w', encoding='utf-8') as f:
                            json.dump(profiles_data, f, ensure_ascii=False, indent=2)
                    else:
                        import csv
                        profiles_data = [p.to_twitter_format() for p in existing_profiles]
                        if profiles_data:
                            fieldnames = list(profiles_data[0].keys())
                            with open(realtime_output_path, 'w', encoding='utf-8', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                                writer.writerows(profiles_data)
                except Exception as e:
                    logger.warning(f"实时保存 profiles 失败: {e}")

        current_locale = get_locale()

        def generate_single_profile(idx: int, entity: EntityNode) -> tuple:
            """生成单个profile的工作函数"""
            set_locale(current_locale)
            entity_type = entity.get_entity_type() or "Entity"

            try:
                profile = self.generate_profile_from_entity(
                    entity=entity,
                    user_id=idx,
                    use_llm=use_llm,
                    sim_type=sim_type
                )

                print_generated_profile(entity.name, entity_type, profile)

                return idx, profile, None

            except Exception as e:
                logger.error(f"生成实体 {entity.name} 的人设失败: {str(e)}")
                fallback_profile = OasisAgentProfile(
                    user_id=idx,
                    user_name=generate_username(entity.name),
                    name=entity.name,
                    bio=f"{entity_type}: {entity.name}",
                    persona=entity.summary or f"A participant in social discussions.",
                    source_entity_uuid=entity.uuid,
                    source_entity_type=entity_type,
                )
                return idx, fallback_profile, str(e)

        logger.info(f"开始并行生成 {total} 个Agent人设（并行数: {parallel_count}）...")
        print(f"\n{'='*60}")
        print(f"开始生成Agent人设 - 共 {total} 个实体，并行数: {parallel_count}")
        print(f"{'='*60}\n")

        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel_count) as executor:
            future_to_entity = {
                executor.submit(generate_single_profile, idx, entity): (idx, entity)
                for idx, entity in enumerate(entities)
            }

            for future in concurrent.futures.as_completed(future_to_entity):
                idx, entity = future_to_entity[future]
                entity_type = entity.get_entity_type() or "Entity"

                try:
                    result_idx, profile, error = future.result()
                    profiles[result_idx] = profile

                    with lock:
                        completed_count[0] += 1
                        current = completed_count[0]

                    save_profiles_realtime()

                    if progress_callback:
                        progress_callback(
                            current,
                            total,
                            f"已完成 {current}/{total}: {entity.name}（{entity_type}）"
                        )

                    if error:
                        logger.warning(f"[{current}/{total}] {entity.name} 使用备用人设: {error}")
                    else:
                        logger.info(f"[{current}/{total}] 成功生成人设: {entity.name} ({entity_type})")

                except Exception as e:
                    logger.error(f"处理实体 {entity.name} 时发生异常: {str(e)}")
                    with lock:
                        completed_count[0] += 1
                    profiles[idx] = OasisAgentProfile(
                        user_id=idx,
                        user_name=generate_username(entity.name),
                        name=entity.name,
                        bio=f"{entity_type}: {entity.name}",
                        persona=entity.summary or "A participant in social discussions.",
                        source_entity_uuid=entity.uuid,
                        source_entity_type=entity_type,
                    )
                    save_profiles_realtime()

        print(f"\n{'='*60}")
        print(f"人设生成完成！共生成 {len([p for p in profiles if p])} 个Agent")
        print(f"{'='*60}\n")

        return profiles

    def save_profiles(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """
        保存Profile到文件（根据平台选择正确格式）
        """
        if platform == "twitter":
            self._save_twitter_csv(profiles, file_path)
        else:
            self._save_reddit_json(profiles, file_path)

    def _save_twitter_csv(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        保存Twitter Profile为CSV格式（符合OASIS官方要求）
        """
        import csv

        if not file_path.endswith('.csv'):
            file_path = file_path.replace('.json', '.csv')

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            headers = ['user_id', 'name', 'username', 'user_char', 'description']
            writer.writerow(headers)

            for idx, profile in enumerate(profiles):
                user_char = profile.bio
                if profile.persona and profile.persona != profile.bio:
                    user_char = f"{profile.bio} {profile.persona}"
                user_char = user_char.replace('\n', ' ').replace('\r', ' ')

                description = profile.bio.replace('\n', ' ').replace('\r', ' ')

                row = [
                    idx,
                    profile.name,
                    profile.user_name,
                    user_char,
                    description
                ]
                writer.writerow(row)

        logger.info(f"已保存 {len(profiles)} 个Twitter Profile到 {file_path} (OASIS CSV格式)")

    def _save_reddit_json(self, profiles: List[OasisAgentProfile], file_path: str):
        """
        保存Reddit Profile为JSON格式
        """
        data = []
        for idx, profile in enumerate(profiles):
            item = {
                "user_id": profile.user_id if profile.user_id is not None else idx,
                "username": profile.user_name,
                "name": profile.name,
                "bio": profile.bio[:150] if profile.bio else f"{profile.name}",
                "persona": profile.persona or f"{profile.name} is a participant in social discussions.",
                "karma": profile.karma if profile.karma else 1000,
                "created_at": profile.created_at,
                "age": profile.age if profile.age else 30,
                "gender": normalize_gender(profile.gender),
                "mbti": profile.mbti if profile.mbti else "ISTJ",
                "country": profile.country if profile.country else "中国",
            }

            if profile.profession:
                item["profession"] = profile.profession
            if profile.interested_topics:
                item["interested_topics"] = profile.interested_topics
            if profile.education_level:
                item["education_level"] = profile.education_level
            if profile.iq_level:
                item["iq_level"] = profile.iq_level
            if profile.cognitive_style:
                item["cognitive_style"] = profile.cognitive_style
            if profile.knowledge_level:
                item["knowledge_level"] = profile.knowledge_level

            data.append(item)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"已保存 {len(profiles)} 个Reddit Profile到 {file_path} (JSON格式，包含user_id字段)")

    def save_profiles_to_json(
        self,
        profiles: List[OasisAgentProfile],
        file_path: str,
        platform: str = "reddit"
    ):
        """[已废弃] 请使用 save_profiles() 方法"""
        logger.warning("save_profiles_to_json已废弃，请使用save_profiles方法")
        self.save_profiles(profiles, file_path, platform)
