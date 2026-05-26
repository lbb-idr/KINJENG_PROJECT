"""
Inner Parliament — Multi-perspective internal debate engine for survey agents.

When an agent receives a survey question, the Inner Parliament:
1. Synthesizer: Understands the question within the agent's context
2. Debaters: 5 internal perspectives debate the answer
3. Chairperson: Synthesizes a final answer from the debate
4. Voter: Weighs perspectives based on agent persona traits
"""

import json
import random
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.cognitive.parliament')


DEBATE_PERSPECTIVES = {
    "rationalist": {
        "name": "Logika",
        "description": "Suara yang mikir pake logika, data, dan bukti-bukti",
        "prompt": (
            "Anda adalah suara LOGIKA dalam diri partisipan. "
            "Anda menganalisis pertanyaan secara logis, menggunakan bukti dan data. "
            "Abaikan emosi dan fokus pada fakta objektif."
        )
    },
    "emotional": {
        "name": "Perasaan",
        "description": "Suara yang ngikutin perasaan dan pengalaman pribadi",
        "prompt": (
            "Anda adalah suara PERASAAN dalam diri partisipan. "
            "Anda merespon berdasarkan perasaan, intuisi, dan pengalaman pribadi. "
            "Abaikan analisis logis dan fokus pada apa yang Anda rasakan."
        )
    },
    "social": {
        "name": "Lingkungan",
        "description": "Suara yang mikirin gimana pandangan orang sekitar",
        "prompt": (
            "Anda adalah suara LINGKUNGAN dalam diri partisipan. "
            "Anda mempertimbangkan apa yang orang lain pikirkan, norma sosial, "
            "dan bagaimana jawaban Anda akan dilihat oleh lingkungan sekitar."
        )
    },
    "skeptic": {
        "name": "Waspada",
        "description": "Suara yang selalu waspada dan nggak gampang percaya",
        "prompt": (
            "Anda adalah suara WASPADA dalam diri partisipan. "
            "Anda mempertanyakan asumsi, mencari kelemahan argumen, "
            "dan tidak mudah percaya tanpa bukti kuat."
        )
    },
    "intuitive": {
        "name": "Naluri",
        "description": "Suara yang ngikutin firasat dan respons spontan",
        "prompt": (
            "Anda adalah suara NALURI dalam diri partisipan. "
            "Anda merespon dengan naluri pertama, tanpa berpikir panjang. "
            "Jawaban Anda cepat, spontan, dan apa adanya."
        )
    }
}


@dataclass
class DebateRound:
    """A single debate round record."""
    timestamp: float
    question: str
    persona_summary: str
    perspectives: Dict[str, str] = field(default_factory=dict)
    chairperson_synthesis: Optional[str] = None
    final_answer: Optional[str] = None
    final_likert_score: Optional[int] = None
    dominant_perspective: Optional[str] = None
    confidence: float = 0.0
    reasoning: Optional[str] = None


class InnerParliament:
    """
    Multi-perspective internal debate engine.
    
    Given a question and an agent persona, runs an internal debate
    between 5 perspectives and produces a final answer.
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        self._llm = None
        self.debate_history: List[DebateRound] = []

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(temperature=0.8)
        return self._llm

    @staticmethod
    def select_perspectives(personality: str, count: int = 3) -> List[str]:
        """Select the most relevant perspectives for a given personality type."""
        personality_map = {
            "Suka Menganalisis": ["rationalist", "skeptic", "intuitive"],
            "Mudah Terbawa Perasaan": ["emotional", "intuitive", "social"],
            "Selalu Bertanya-tanya": ["skeptic", "rationalist", "intuitive"],
            "Semangat": ["social", "emotional", "intuitive"],
            "Praktis": ["rationalist", "skeptic", "social"],
            "Cuek": ["skeptic", "intuitive", "rationalist"],
            "Ideal": ["emotional", "social", "rationalist"]
        }
        base = personality_map.get(personality, ["rationalist", "emotional", "social"])
        return base[:count]

    @staticmethod
    def calculate_likert_from_debate(
        perspectives: Dict[str, str],
        agent_persona: Dict[str, Any],
        scale: int = 5
    ) -> Tuple[int, float, str]:
        """
        Calculate Likert score from multiple perspectives, weighted by persona.
        
        Returns: (score, confidence, reasoning)
        """
        perspective_weights = {
            "rationalist": 1.2 if agent_persona.get("personality") == "Suka Menganalisis" else 0.8,
            "emotional": 1.3 if agent_persona.get("personality") == "Mudah Terbawa Perasaan" else 0.7,
            "social": 1.1 if agent_persona.get("personality") in ["Semangat", "Ideal"] else 0.8,
            "skeptic": 1.2 if agent_persona.get("personality") in ["Selalu Bertanya-tanya", "Suka Menganalisis"] else 0.7,
            "intuitive": 1.0
        }

        scores = []
        weights = []
        for perspective_key, text in perspectives.items():
            if not text:
                continue
            weight = perspective_weights.get(perspective_key, 1.0)
            sentiment = _estimate_sentiment(text)
            score = max(1, min(scale, round(sentiment * scale)))
            scores.append(score)
            weights.append(weight)

        if not scores:
            return scale // 2 + 1, 0.3, "Perspectives unavailable, using middle score"

        weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        final_score = max(1, min(scale, round(weighted_avg)))
        confidence = min(1.0, (max(weights) / sum(weights)) * len(scores) / 3)
        dominant = max(perspectives, key=lambda k: perspective_weights.get(k, 1.0))

        reasoning_parts = []
        for pk in perspectives:
            wt = perspective_weights.get(pk, 1.0)
            reasoning_parts.append(f"{DEBATE_PERSPECTIVES[pk]['name']}(bobot={wt:.1f})")
        
        reasoning = f"Debat: {', '.join(reasoning_parts)} → skor {final_score}/{scale} (confidence={confidence:.2f})"
        return final_score, confidence, reasoning

    def debate(self, question: str, persona: Dict[str, Any], likert_scale: int = 5) -> DebateRound:
        """
        Run inner parliament debate for a given question and persona.
        
        Args:
            question: The survey question
            persona: Agent persona dict (age, gender, personality, etc.)
            likert_scale: Likert scale (5 or 7)
            
        Returns:
            DebateRound with final answer
        """
        personality = persona.get("personality", "Praktis")
        perspective_keys = self.select_perspectives(personality, count=3)
        
        persona_summary = (
            f"Usia: {persona.get('age', '?')}, "
            f"Kelamin: {persona.get('gender', '?')}, "
            f"Pendidikan: {persona.get('education', '?')}, "
            f"Pekerjaan: {persona.get('occupation', '?')}, "
            f"Kepribadian: {personality}, "
            f"Ciri: {persona.get('trait', '?')}, "
            f"Pengetahuan: {persona.get('knowledge_level', '?')}, "
            f"Opini: {persona.get('opinion_bias', '?')}, "
            f"Pengaruh: {persona.get('social_influence', '?')}"
        )

        round_data = DebateRound(
            timestamp=time.time(),
            question=question,
            persona_summary=persona_summary
        )

        if self.use_llm:
            round_data = self._llm_debate(round_data, persona, question, perspective_keys, likert_scale)
        else:
            round_data = self._rule_based_debate(round_data, persona, question, perspective_keys, likert_scale)

        self.debate_history.append(round_data)
        return round_data

    def _llm_debate(
        self,
        round_data: DebateRound,
        persona: Dict[str, Any],
        question: str,
        perspective_keys: List[str],
        likert_scale: int
    ) -> DebateRound:
        llm = self._get_llm()
        scale_labels = {1: "Sangat Tidak Setuju", 2: "Tidak Setuju", 3: "Netral", 4: "Setuju", 5: "Sangat Setuju"}
        if likert_scale == 7:
            scale_labels = {1: "STS", 2: "TS", 3: "ATS", 4: "N", 5: "AS", 6: "S", 7: "SS"}

        system_base = (
            f"Anda adalah partisipan survei dengan profil berikut:\n"
            f"{round_data.persona_summary}\n\n"
            f"Skala Likert {likert_scale}-point: "
            f"{', '.join(f'{k}={v}' for k, v in scale_labels.items())}\n\n"
            f"Jawab dengan format:\n"
            f"LIKERT: <angka>\n"
            f"ALASAN: <penjelasan singkat 1-2 kalimat>"
        )

        final_responses = []
        for pk in perspective_keys:
            perspective = DEBATE_PERSPECTIVES[pk]
            try:
                response = llm.chat(
                    messages=[
                        {"role": "system", "content": f"{system_base}\n\n{perspective['prompt']}"},
                        {"role": "user", "content": f"Pertanyaan: {question}\n\nBagaimana RESPON ANDA sebagai suara {perspective['name']}? Pilih satu angka Likert dan berikan alasan singkat."}
                    ],
                    temperature=0.9,
                    max_tokens=300
                )
                round_data.perspectives[pk] = response.strip()
                final_responses.append(response.strip())
            except Exception as e:
                logger.warning(f"Perspective {pk} failed: {e}")
                round_data.perspectives[pk] = ""
                final_responses.append("")

        score, confidence, reasoning = self.calculate_likert_from_debate(
            round_data.perspectives, persona, likert_scale
        )
        round_data.final_likert_score = score
        round_data.confidence = confidence
        round_data.reasoning = reasoning
        round_data.dominant_perspective = max(
            round_data.perspectives,
            key=lambda k: len(round_data.perspectives.get(k, ""))
        ) if any(round_data.perspectives.values()) else "rationalist"

        try:
            synthesis = llm.chat(
                messages=[
                    {"role": "system", "content": system_base + "\n\nAnda adalah KETUA PARLEMEN yang menyimpulkan debat internal."},
                    {"role": "user", "content": (
                        f"Pertanyaan: {question}\n\n"
                        f"Hasil debat internal:\n" +
                        "\n".join(f"Suara {DEBATE_PERSPECTIVES[k]['name']}: {v}" for k, v in round_data.perspectives.items() if v) +
                        f"\n\nSkor Likert akhir: {score}\n"
                        f"Buat satu kalimat kesimpulan yang mencerminkan jawaban partisipan."
                    )}
                ],
                temperature=0.5,
                max_tokens=200
            )
            round_data.chairperson_synthesis = synthesis.strip()
        except Exception as e:
            logger.warning(f"Synthesis failed: {e}")
            round_data.chairperson_synthesis = f"Berdasarkan pertimbangan internal, skor {score} dipilih."

        round_data.final_answer = f"LIKERT: {score} | {round_data.chairperson_synthesis}"
        return round_data

    def _rule_based_debate(
        self,
        round_data: DebateRound,
        persona: Dict[str, Any],
        question: str,
        perspective_keys: List[str],
        likert_scale: int
    ) -> DebateRound:
        """Lightweight rule-based debate simulation (no LLM needed)."""
        opinion_bias_map = {
            "Hati-hati": 0.6, "Seimbang": 0.5, "Terbuka": 0.4, "Netral": 0.5
        }
        knowledge_map = {"Rendah": 0.3, "Sedang": 0.5, "Tinggi": 0.7, "Ahli": 0.85}

        base_bias = opinion_bias_map.get(persona.get("opinion_bias", "Seimbang"), 0.5)
        knowledge = knowledge_map.get(persona.get("knowledge_level", "Sedang"), 0.5)

        perspective_sentiments = {
            "rationalist": base_bias * (0.7 + 0.3 * knowledge),
            "emotional": base_bias * random.uniform(0.4, 1.0),
            "social": base_bias * random.uniform(0.5, 0.9),
            "skeptic": base_bias * (0.3 + 0.5 * knowledge),
            "intuitive": base_bias * random.uniform(0.3, 0.8)
        }

        for pk in perspective_keys:
            sentiment = perspective_sentiments.get(pk, 0.5)
            score = max(1, min(likert_scale, round(sentiment * likert_scale)))
            sentiment_label = "setuju" if score > likert_scale // 2 else "tidak setuju" if score < likert_scale // 2 else "netral"
            round_data.perspectives[pk] = f"Skor {score}/{likert_scale} — cenderung {sentiment_label}"

        score, confidence, reasoning = self.calculate_likert_from_debate(
            round_data.perspectives, persona, likert_scale
        )
        round_data.final_likert_score = score
        round_data.confidence = confidence
        round_data.reasoning = reasoning
        round_data.dominant_perspective = perspective_keys[0] if perspective_keys else "rationalist"
        round_data.chairperson_synthesis = (
            f"Setelah mempertimbangkan berbagai perspektif, "
            f"partisipan cenderung memberikan skor {score}."
        )
        round_data.final_answer = f"LIKERT: {score} | {round_data.chairperson_synthesis}"
        return round_data

    def get_debate_summary(self, round_index: int = -1) -> Optional[str]:
        """Get a readable summary of a debate round."""
        if not self.debate_history:
            return None
        round_data = self.debate_history[round_index]
        lines = [
            f"Pertanyaan: {round_data.question}",
            f"Profil: {round_data.persona_summary}",
            "--- Debat Internal ---"
        ]
        for pk, text in round_data.perspectives.items():
            name = DEBATE_PERSPECTIVES.get(pk, {}).get("name", pk)
            lines.append(f"  [{name}]: {text}")
        lines.append(f"--- Keputusan ---")
        lines.append(f"Skor Likert: {round_data.final_likert_score}")
        lines.append(f"Keyakinan: {round_data.confidence:.2f}")
        lines.append(f"Kesimpulan: {round_data.chairperson_synthesis}")
        return "\n".join(lines)


def _estimate_sentiment(text: str) -> float:
    """Rough sentiment estimation (0.0 = negative, 1.0 = positive)."""
    if not text:
        return 0.5
    positive_words = {"setuju", "baik", "penting", "suka", "benar", "iya", "positif", "mendukung", "pantas", "ya"}
    negative_words = {"tidak", "kurang", "buruk", "salah", "negatif", "menolak", "tidak setuju", "bukan", "jangan", "enggak"}
    text_lower = text.lower()
    words = text_lower.split()
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    if pos_count + neg_count == 0:
        return 0.5
    return pos_count / (pos_count + neg_count)
