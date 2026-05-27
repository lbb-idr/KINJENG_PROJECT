"""
Survey Debate Platform — Multi-agent public debate for survey questions.

Replaces Inner Parliament (internal voices in 1 agent) with actual
multi-agent debate between simulation agents, displayed as Twitter-style
bubble chat in the frontend.

Flow per question:
1. Select 5 agents relevant to the question
2. Round 1: Each agent posts their opinion
3. Round 2: Each agent replies to others' posts
4. Chairperson reads all posts → determines Likert score
5. Debate transcript + result stored for frontend polling
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from .agent_identity import get_identity_context, get_signature, build_agent_identity

logger = get_logger('kinjeng.survey_debate')


@dataclass
class DebatePost:
    round_num: int
    agent_id: str
    agent_name: str
    content: str
    timestamp: float = 0.0
    post_id: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()
        if not self.post_id:
            self.post_id = uuid.uuid4().hex[:12]


@dataclass
class DebateSession:
    session_id: str
    question_id: str
    question_text: str
    likert_scale: int = 5
    status: str = "pending"  # selecting → ready → round1 → round2 → chairperson → complete
    posts: List[DebatePost] = field(default_factory=list)
    agents: List[Dict[str, Any]] = field(default_factory=list)
    confirmed_count: int = 0  # jumlah agent yg sudah dikonfirmasi user
    likert_score: Optional[int] = None
    confidence: float = 0.0
    chairperson_conclusion: Optional[str] = None
    created_at: float = 0.0
    completed_at: Optional[float] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


DEBATE_DIR = os.path.join(Config.UPLOAD_FOLDER, 'survey_debates')


class SurveyDebateService:
    """Orchestrates multi-agent debates for survey questions."""

    DEBATE_AGENT_COUNT = 5
    DEBATE_ROUNDS = 2

    def __init__(self):
        os.makedirs(DEBATE_DIR, exist_ok=True)
        self._llm = None

    def _get_llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = LLMClient(temperature=0.8)
        return self._llm

    # ── Session management ──────────────────────────────

    def create_session(
        self,
        question_id: str,
        question_text: str,
        agents: List[Dict[str, Any]],
        likert_scale: int = 5
    ) -> DebateSession:
        session = DebateSession(
            session_id=f"deb_{uuid.uuid4().hex[:12]}",
            question_id=question_id,
            question_text=question_text,
            likert_scale=likert_scale,
            agents=agents[:self.DEBATE_AGENT_COUNT],
            status="selecting"
        )
        self._save_session(session)
        logger.info(f"Debate session created: {session.session_id} for Q: {question_text[:50]}")
        return session

    # ── Agent confirmation ────────────────────────────

    def confirm_agent(self, session_id: str) -> DebateSession:
        """Confirm the next unconfirmed agent. Returns updated session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        if session.status != "selecting":
            raise ValueError(f"Session {session_id} is not in selecting status")
        if session.confirmed_count >= len(session.agents):
            raise ValueError("All agents already confirmed")

        session.confirmed_count += 1
        if session.confirmed_count >= len(session.agents):
            session.status = "ready"
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[DebateSession]:
        path = os.path.join(DEBATE_DIR, f"{session_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self._dict_to_session(data)

    def get_all_sessions(self, project_id: str) -> List[DebateSession]:
        sessions = []
        for fname in os.listdir(DEBATE_DIR):
            if fname.endswith('.json'):
                sess = self.get_session(fname[:-5])
                if sess:
                    sessions.append(sess)
        return sessions

    # ── Debate execution ────────────────────────────────

    def run_debate(self, session_id: str) -> DebateSession:
        """Run all debate rounds and chairperson for a session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        # Auto-confirm all agents if still in selecting (batch mode)
        if session.status == "selecting" or session.confirmed_count < len(session.agents):
            session.confirmed_count = len(session.agents)
            session.status = "ready"
            self._save_session(session)

        # Round 1: each agent posts initial opinion
        logger.info(f"Debate {session_id}: Round 1 starting")
        session = self._run_round(session, round_num=1)

        # Round 2: agents reply to each other
        logger.info(f"Debate {session_id}: Round 2 starting")
        session = self._run_round(session, round_num=2)

        # Chairperson: reads all posts → determines score
        logger.info(f"Debate {session_id}: Chairperson analyzing")
        session = self._run_chairperson(session)

        session.status = "complete"
        session.completed_at = time.time()
        self._save_session(session)
        logger.info(f"Debate {session_id} complete → score {session.likert_score}/{session.likert_scale}")
        return session

    # ── Internal round logic ────────────────────────────

    def _run_round(self, session: DebateSession, round_num: int) -> DebateSession:
        llm = self._get_llm()
        scale = session.likert_scale

        for agent in session.agents:
            persona = self._format_persona(agent)
            other_posts = self._get_other_posts(session, agent.get("user_id"), round_num)

            prompt = (
                f"Anda adalah {agent.get('name', 'partisipan')}.\n"
                f"Profil: {persona}\n\n"
                f"Pertanyaan survei: {session.question_text}\n"
                f"Skala Likert 1-{scale} (1=Sangat Tidak Setuju, {scale}=Sangat Setuju)\n\n"
            )

            if round_num == 1:
                prompt += (
                    f"Berikan OPINI ANDA tentang pertanyaan ini sebagai {agent.get('name', 'partisipan')}.\n"
                    f"Tulis 2-3 kalimat dari sudut pandang pribadi Anda, seolah Anda sedang posting di Twitter.\n"
                    f"Akhiri dengan: LIKERT: <angka>"
                )
            else:
                prompt += (
                    f"Setelah membaca pendapat agen lain:\n{other_posts}\n\n"
                    f"Tanggapi atau rebuttal pendapat mereka. Tulis 2-3 kalimat.\n"
                    f"Akhiri dengan: LIKERT: <angka>"
                )

            try:
                response = llm.chat(messages=[
                    {"role": "system", "content": "Anda adalah partisipan survei yang sedang berdebat di platform sosial."},
                    {"role": "user", "content": prompt}
                ], temperature=0.9, max_tokens=300)
                content = response.strip()
            except Exception as e:
                logger.warning(f"Agent {agent.get('name')} round {round_num} failed: {e}")
                content = f"Maaf, saya belum bisa memberikan pendapat saat ini. LIKERT: {scale // 2 + 1}"

            session.posts.append(DebatePost(
                round_num=round_num,
                agent_id=str(agent.get("user_id", "")),
                agent_name=agent.get("name", agent.get("username", "Unknown")),
                content=content
            ))

        session.status = f"round{round_num + 1}" if round_num < 2 else "chairperson"
        self._save_session(session)
        return session

    def _run_chairperson(self, session: DebateSession) -> DebateSession:
        llm = self._get_llm()
        scale = session.likert_scale

        transcript = self._format_transcript(session)
        agent_identities = "\n".join(
            f"- {a.get('name', '?' )}: "
            f"Usia {a.get('age', '?')}, {a.get('profession', a.get('occupation', '?'))}, "
            f"Opini {a.get('opinion_bias', '?')}"
            for a in session.agents
        )
        prompt = (
            f"Anda adalah KETUA DEBAT yang membaca seluruh diskusi publik antara "
            f"{len(session.agents)} partisipan tentang pertanyaan survei:\n\n"
            f"Pertanyaan: {session.question_text}\n\n"
            f"Identitas partisipan:\n{agent_identities}\n\n"
            f"Berikut transkrip debat:\n{transcript}\n\n"
            f"Tugas Anda:\n"
            f"1. Analisis semua argumen yang muncul\n"
            f"2. Tentukan skor Likert 1-{scale} yang paling mewakili konsensus\n"
            f"3. Berikan kesimpulan 2-3 kalimat\n\n"
            f"Format:\n"
            f"LIKERT: <angka>\n"
            f"KESIMPULAN: <kesimpulan>"
        )

        try:
            response = llm.chat(messages=[
                {"role": "system", "content": "Anda adalah ketua debat yang netral dan analitis."},
                {"role": "user", "content": prompt}
            ], temperature=0.5, max_tokens=500)
            result = response.strip()
        except Exception as e:
            logger.warning(f"Chairperson failed: {e}")
            result = f"LIKERT: {scale // 2 + 1}\nKESIMPULAN: Berdasarkan diskusi, skor netral dipilih."

        score = self._extract_likert(result, scale)
        session.likert_score = score
        session.confidence = 0.7
        session.chairperson_conclusion = result
        return session

    # ── Helpers ─────────────────────────────────────────

    def _format_persona(self, agent: Dict[str, Any]) -> str:
        agent_id = str(agent.get('user_id', ''))
        identity_ctx = get_identity_context(agent_id)
        return (
            f"Usia: {agent.get('age', '?')}, "
            f"Pekerjaan: {agent.get('profession', agent.get('occupation', '?'))}, "
            f"Kepribadian: {agent.get('personality', agent.get('mbti', '?'))}, "
            f"Opini: {agent.get('opinion_bias', 'Seimbang')}\n"
            f"{identity_ctx}"
        )

    def _get_other_posts(self, session: DebateSession, agent_user_id, round_num: int) -> str:
        posts = [
            p for p in session.posts
            if p.round_num == round_num and p.agent_id != str(agent_user_id)
        ]
        if not posts:
            return "(belum ada postingan dari agen lain)"
        return "\n".join(f"- {p.agent_name}: {p.content[:200]}" for p in posts)

    def _format_transcript(self, session: DebateSession) -> str:
        lines = []
        for p in sorted(session.posts, key=lambda x: (x.round_num, x.timestamp)):
            lines.append(f"[Ron {p.round_num}] {p.agent_name}: {p.content}")
        return "\n\n".join(lines)

    def _extract_likert(self, text: str, scale: int) -> int:
        import re
        m = re.search(r'LIKERT:\s*(\d+)', text, re.IGNORECASE)
        if m:
            return max(1, min(scale, int(m.group(1))))
        return scale // 2 + 1

    def _save_session(self, session: DebateSession):
        path = os.path.join(DEBATE_DIR, f"{session.session_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": session.session_id,
                "question_id": session.question_id,
                "question_text": session.question_text,
                "likert_scale": session.likert_scale,
                "status": session.status,
                "agents": session.agents,
                "confirmed_count": session.confirmed_count,
                "posts": [asdict(p) for p in session.posts],
                "likert_score": session.likert_score,
                "confidence": session.confidence,
                "chairperson_conclusion": session.chairperson_conclusion,
                "created_at": session.created_at,
                "completed_at": session.completed_at
            }, f, ensure_ascii=False, indent=2)

    def _dict_to_session(self, data: Dict) -> DebateSession:
        posts = [DebatePost(**p) for p in data.get("posts", [])]
        return DebateSession(
            session_id=data["session_id"],
            question_id=data["question_id"],
            question_text=data["question_text"],
            likert_scale=data.get("likert_scale", 5),
            status=data.get("status", "pending"),
            posts=posts,
            agents=data.get("agents", []),
            confirmed_count=data.get("confirmed_count", 0),
            likert_score=data.get("likert_score"),
            confidence=data.get("confidence", 0.0),
            chairperson_conclusion=data.get("chairperson_conclusion"),
            created_at=data.get("created_at", 0.0),
            completed_at=data.get("completed_at")
        )

    # ── Agent selection ─────────────────────────────────

    def select_debate_agents(
        self,
        question_text: str,
        all_agents: List[Dict[str, Any]],
        count: int = None
    ) -> List[Dict[str, Any]]:
        """Select the most relevant agents for debating a question."""
        count = count or self.DEBATE_AGENT_COUNT
        if len(all_agents) <= count:
            return all_agents

        import re
        keywords = set(re.findall(r'\w+', question_text.lower()))
        scored = []
        for agent in all_agents:
            score = 0
            profile_text = (
                f"{agent.get('bio', '')} {agent.get('persona', '')} "
                f"{' '.join(agent.get('interested_topics', []))} "
                f"{agent.get('profession', agent.get('occupation', ''))}"
            ).lower()
            for kw in keywords:
                if len(kw) > 3 and kw in profile_text:
                    score += 1
            scored.append((score, agent))

        scored.sort(key=lambda x: -x[0])
        return [a for _, a in scored[:count]]
