"""
Cognitive Pipeline — Orchestrates the full think → debate → answer pipeline for survey agents.
"""

import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from .inner_parliament import InnerParliament, DebateRound
from .survey_memory import SurveyMemory

logger = get_logger('mirofish.cognitive.pipeline')


@dataclass
class SurveyResponse:
    """Complete survey response from one agent."""
    agent_id: str
    question_id: str
    question_text: str
    likert_score: Optional[int] = None
    text_answer: Optional[str] = None
    answer: Optional[str] = None
    confidence: float = 0.0
    debate_round: Optional[DebateRound] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class CognitivePipeline:
    """
    Full cognitive pipeline for survey agents.
    
    Flow:
    1. Load agent profile and memory
    2. Run Inner Parliament debate
    3. Generate final answer
    4. Store in episodic memory
    5. Optionally trigger reflection
    """

    def __init__(self, use_llm: bool = True, enable_reflection: bool = False):
        self.use_llm = use_llm
        self.enable_reflection = enable_reflection
        self.parliament = InnerParliament(use_llm=use_llm)
        self._llm = None

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(temperature=0.7)
        return self._llm

    def process_question(
        self,
        agent_id: str,
        agent_persona: Dict[str, Any],
        question: Dict[str, Any],
        memory: Optional[SurveyMemory] = None,
        likert_scale: int = 5
    ) -> SurveyResponse:
        """
        Process a single survey question through the cognitive pipeline.
        
        Args:
            agent_id: Unique agent identifier
            agent_persona: Agent persona dict (age, gender, personality, etc.)
            question: Question dict with id, text, type, scale, etc.
            memory: Optional SurveyMemory instance for this agent
            likert_scale: Likert scale (5 or 7)
            
        Returns:
            SurveyResponse with the agent's answer
        """
        start_time = time.time()
        q_id = question.get("id", "unknown")
        q_text = question.get("text", "")
        q_type = question.get("type", "likert")

        response = SurveyResponse(
            agent_id=agent_id,
            question_id=q_id,
            question_text=q_text
        )

        try:
            if q_type == "likert":
                result = self._handle_likert(agent_id, agent_persona, q_text, memory, likert_scale)
                response.likert_score = result["score"]
                response.answer = result["final_answer"]
                response.text_answer = result.get("text_answer")
                response.confidence = result["confidence"]
                response.debate_round = result.get("debate_round")

            elif q_type == "mcq":
                result = self._handle_mcq(agent_id, agent_persona, q_text, question.get("options", []), memory)
                response.answer = result["answer"]
                response.text_answer = result["answer"]
                response.confidence = result["confidence"]

            elif q_type == "open":
                result = self._handle_open(agent_id, agent_persona, q_text, memory, question.get("max_length", 500))
                response.text_answer = result["answer"]
                response.answer = result["answer"]
                response.confidence = result["confidence"]

            elif q_type == "demographic":
                result = self._handle_demographic(agent_persona, q_text)
                response.answer = result["answer"]
                response.text_answer = result["answer"]
                response.confidence = 1.0

            else:
                response.answer = ""
                response.error = f"Unknown question type: {q_type}"

            if memory and response.answer is not None:
                memory.add_episodic(
                    question=q_text,
                    answer=str(response.answer),
                    question_id=q_id,
                    likert_score=response.likert_score,
                    confidence=response.confidence
                )

        except Exception as e:
            logger.error(f"Pipeline error for {agent_id}/{q_id}: {e}")
            response.error = str(e)
            response.answer = ""

        response.processing_time_ms = (time.time() - start_time) * 1000
        return response

    def process_batch(
        self,
        agent_id: str,
        agent_persona: Dict[str, Any],
        questions: List[Dict[str, Any]],
        memory: Optional[SurveyMemory] = None,
        likert_scale: int = 5
    ) -> List[SurveyResponse]:
        """Process multiple questions for one agent."""
        return [
            self.process_question(agent_id, agent_persona, q, memory, likert_scale)
            for q in questions
        ]

    def _handle_likert(
        self,
        agent_id: str,
        persona: Dict[str, Any],
        question: str,
        memory: Optional[SurveyMemory],
        likert_scale: int
    ) -> Dict[str, Any]:
        debate_round = self.parliament.debate(question, persona, likert_scale)
        memory_context = memory.get_context_block() if memory else ""

        text_answer = None
        if self.use_llm:
            try:
                llm = self._get_llm()
                result = llm.chat(
                    messages=[
                        {"role": "system", "content": (
                            f"Anda adalah partisipan survei. Profil:\n"
                            f"{debate_round.persona_summary}\n\n"
                            f"{memory_context}\n\n"
                            f"Jawab pertanyaan berikut dengan 1-2 kalimat singkat dan natural."
                        )},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.8,
                    max_tokens=200
                )
                text_answer = result.strip()
            except Exception as e:
                logger.warning(f"Open text generation failed: {e}")

        if debate_round.final_answer:
            text_answer = text_answer or debate_round.final_answer

        return {
            "score": debate_round.final_likert_score,
            "confidence": debate_round.confidence,
            "final_answer": debate_round.final_answer,
            "text_answer": text_answer,
            "debate_round": debate_round
        }

    def _handle_mcq(
        self,
        agent_id: str,
        persona: Dict[str, Any],
        question: str,
        options: List[str],
        memory: Optional[SurveyMemory]
    ) -> Dict[str, Any]:
        if not options:
            return {"answer": "", "confidence": 0.0}

        idx_offset = persona.get("age", 30) % len(options)
        opinion_bias = persona.get("opinion_bias", "Seimbang")
        
        if opinion_bias == "Hati-hati":
            idx = 0
        elif opinion_bias == "Terbuka":
            idx = len(options) - 1
        elif opinion_bias == "Seimbang":
            idx = len(options) // 2
        else:
            idx = (idx_offset + hash(question) % len(options)) % len(options)

        return {
            "answer": options[idx],
            "confidence": 0.7
        }

    def _handle_open(
        self,
        agent_id: str,
        persona: Dict[str, Any],
        question: str,
        memory: Optional[SurveyMemory],
        max_length: int = 500
    ) -> Dict[str, Any]:
        memory_context = memory.get_context_block() if memory else ""
        persona_summary = (
            f"Usia: {persona.get('age', '?')}, "
            f"Pekerjaan: {persona.get('occupation', '?')}, "
            f"Kepribadian: {persona.get('personality', '?')}, "
            f"Opini: {persona.get('opinion_bias', '?')}"
        )

        if self.use_llm:
            try:
                llm = self._get_llm()
                result = llm.chat(
                    messages=[
                        {"role": "system", "content": (
                            f"Anda adalah partisipan survei.\n{persona_summary}\n\n"
                            f"{memory_context}\n\n"
                            f"Jawab dengan 1-3 kalimat alami seperti manusia biasa. "
                            f"Maksimal {max_length} karakter."
                        )},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.9,
                    max_tokens=200
                )
                return {"answer": result.strip()[:max_length], "confidence": 0.8}
            except Exception as e:
                logger.warning(f"Open answer LLM failed: {e}")

        fallback_responses = [
            "Menurut saya ini topik yang menarik untuk didiskusikan lebih lanjut.",
            "Saya punya pendapat tentang ini, tapi saya perlu informasi lebih dulu.",
            "Saya rasa ini tergantung pada situasi dan kondisinya.",
            "Ini pertanyaan yang bagus. Saya akan memikirkannya.",
            "Dari pengalaman saya, hal ini cukup kompleks."
        ]
        idx = hash(persona.get("agent_id", "") + question) % len(fallback_responses)
        return {"answer": fallback_responses[idx], "confidence": 0.5}

    def _handle_demographic(
        self,
        persona: Dict[str, Any],
        question: str
    ) -> Dict[str, Any]:
        q_lower = question.lower()
        if "usia" in q_lower or "umur" in q_lower or "age" in q_lower:
            return {"answer": str(persona.get("age", 30)), "confidence": 1.0}
        if "kelamin" in q_lower or "gender" in q_lower:
            return {"answer": persona.get("gender", "Laki-laki"), "confidence": 1.0}
        if "pendidikan" in q_lower or "education" in q_lower:
            return {"answer": persona.get("education", "S1"), "confidence": 1.0}
        if "pekerjaan" in q_lower or "occupation" in q_lower:
            return {"answer": persona.get("occupation", "Karyawan Swasta"), "confidence": 1.0}
        return {"answer": "", "confidence": 0.5}


class SurveyEngine:
    """
    Orchestrates survey simulation across multiple agents.
    Manages personas, memories, and the cognitive pipeline.
    """

    def __init__(self, project_id: str, use_llm: bool = True):
        self.project_id = project_id
        self.pipeline = CognitivePipeline(use_llm=use_llm)
        self.memory_store = None
        self.personas: List[Dict[str, Any]] = []
        self.survey_config: Optional[Dict[str, Any]] = None

    def load_survey(self, survey_config: Dict[str, Any]):
        self.survey_config = survey_config

    def load_personas(self, personas: List[Dict[str, Any]]):
        self.personas = personas
        self.memory_store = __import__('app.services.survey_memory', fromlist=['SurveyMemoryStore']).SurveyMemoryStore(self.project_id)

    def run_survey(
        self,
        question_ids: Optional[List[str]] = None,
        agent_ids: Optional[List[str]] = None,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Run the full survey simulation.
        
        Args:
            question_ids: Filter to specific questions (None = all)
            agent_ids: Filter to specific agents (None = all)
            batch_size: Agents per batch
            
        Returns:
            Complete survey results
        """
        if not self.survey_config or not self.personas:
            return {"error": "Survey config and personas must be loaded first"}

        questions = [
            q for section in self.survey_config.get("sections", [])
            for q in section.get("questions", [])
        ]
        if question_ids:
            questions = [q for q in questions if q.get("id") in question_ids]

        likert_scale = self.survey_config.get("params", {}).get("likertScale", 5)
        target_agents = [
            p for p in self.personas
            if agent_ids is None or p.get("agent_id") in agent_ids
        ]

        results = []
        total = len(target_agents)
        for i, persona in enumerate(target_agents):
            agent_id = persona.get("agent_id", f"agent_{i}")
            agent_name = f"{persona.get('age', '?')}yo_{persona.get('occupation', '?')}"
            memory = self.memory_store.get(agent_id, agent_name) if self.memory_store else None

            responses = self.pipeline.process_batch(
                agent_id=agent_id,
                agent_persona=persona,
                questions=questions,
                memory=memory,
                likert_scale=likert_scale
            )

            results.append({
                "agent_id": agent_id,
                "persona": {k: v for k, v in persona.items() if k != "agent_id"},
                "responses": [
                    {
                        "question_id": r.question_id,
                        "question": r.question_text,
                        "answer": r.answer,
                        "likert_score": r.likert_score,
                        "text_answer": r.text_answer,
                        "confidence": r.confidence,
                        "processing_time_ms": r.processing_time_ms
                    }
                    for r in responses
                ]
            })

            if (i + 1) % batch_size == 0:
                logger.info(f"Survey progress: {i + 1}/{total} agents processed")

        if self.memory_store:
            self.memory_store.save_all()

        return {
            "project_id": self.project_id,
            "total_agents": total,
            "total_questions": len(questions),
            "likert_scale": likert_scale,
            "results": results
        }
