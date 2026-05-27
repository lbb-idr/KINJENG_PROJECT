"""
Survey Service
Manages academic survey templates, question banks, and agent persona templates.
"""

import json
import os
import random
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.api.survey')

ACADEMIC_TEMPLATES = {
    "likert_5": {
        "label": "Likert 1-5",
        "type": "likert",
        "scale": [1, 2, 3, 4, 5],
        "labels": ["Sangat Tidak Setuju", "Tidak Setuju", "Netral", "Setuju", "Sangat Setuju"]
    },
    "likert_7": {
        "label": "Likert 1-7",
        "type": "likert",
        "scale": [1, 2, 3, 4, 5, 6, 7],
        "labels": ["STS", "TS", "ATS", "N", "AS", "S", "SS"]
    },
    "multiple_choice": {
        "label": "Multiple Choice",
        "type": "mcq",
        "options": []
    },
    "open_ended": {
        "label": "Open Ended",
        "type": "open",
        "max_length": 500
    },
    "demographic": {
        "label": "Demographic",
        "type": "demographic",
        "fields": ["age", "gender", "education", "occupation"]
    }
}


class SurveyTemplateService:
    """Service for generating and managing academic survey templates."""

    SURVEYS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'surveys')

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.SURVEYS_DIR, exist_ok=True)

    @classmethod
    def get_available_templates(cls) -> Dict[str, Any]:
        """Return the available question type templates."""
        return ACADEMIC_TEMPLATES

    @classmethod
    def generate_survey(cls, requirement: str, sim_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a survey configuration from a natural language requirement using LLM.
        
        Args:
            requirement: Natural language simulation requirement
            sim_type: Simulation type (academic, political, market, social, custom)
            params: Survey parameters (agent_count, max_rounds, platform, likert_scale)
            
        Returns:
            Survey configuration dict with questions, demographics, etc.
        """
        scale = params.get('likertScale', 5)
        template = ACADEMIC_TEMPLATES[f"likert_{scale}"]
        
        system_prompt = f"""Anda adalah perancang survei akademik. Buat rancangan survei berdasarkan kebutuhan riset berikut.

Simulasi: {requirement}
Tipe: {sim_type}
Skala Likert: {scale}-point ({', '.join(template['labels'])})
Jumlah agen: {params.get('agentCount', 500)}

Buat output JSON dengan struktur:
- title: Judul survei
- description: Deskripsi singkat
- sections: daftar section, masing-masing dengan:
  - id: string unik
  - title: judul section
  - questions: daftar pertanyaan, masing-masing dengan:
    - id: string unik
    - type: "likert" | "mcq" | "open" | "demographic"
    - text: teks pertanyaan
    - scale: [1, 2, 3, ...] (untuk likert)
    - labels: label skala (untuk likert)
    - options: [daftar opsi] (untuk mcq)
    - required: boolean
- demographics: daftar field demografi yang diperlukan
- hypotheses: daftar hipotesis penelitian (min 3)

Pertanyaan harus:
1. Relevan dengan topik riset
2. Mengikuti kaidah metodologi survei
3. Variatif (campuran likert, mcq, open-ended)
4. Minimal 10 pertanyaan inti + 3 demografi + 1 open-ended"""

        try:
            llm = LLMClient(temperature=0.7)
            response = llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Buat survei untuk riset: {requirement}"}
                ],
                response_format={"type": "json_object"}
            )
            
            survey = json.loads(response)
            survey['sim_type'] = sim_type
            survey['params'] = params
            return survey

        except Exception as e:
            logger.error(f"Survey generation failed: {e}")
            return cls._fallback_survey(requirement, sim_type, params)

    @classmethod
    def _fallback_survey(cls, requirement: str, sim_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a basic survey when LLM is unavailable."""
        scale = params.get('likertScale', 5)
        template = ACADEMIC_TEMPLATES[f"likert_{scale}"]
        topic = requirement[:80] if requirement else "topik riset"

        return {
            "title": f"Survei: {topic}",
            "description": f"Survei akademik untuk menganalisis: {requirement}",
            "sim_type": sim_type,
            "params": params,
            "sections": [
                {
                    "id": "persepsi",
                    "title": "Persepsi terhadap " + topic,
                    "questions": [
                        {
                            "id": "q01",
                            "type": "likert",
                            "text": f"Saya memahami isu tentang: {topic}",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q02",
                            "type": "likert",
                            "text": f"Topik '{topic}' relevan dengan kehidupan saya sehari-hari",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q03",
                            "type": "mcq",
                            "text": f"Seberapa sering Anda terpapar informasi tentang '{topic}'?",
                            "options": ["Tidak pernah", "Jarang", "Kadang-kadang", "Sering", "Sangat sering"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "opini",
                    "title": f"Opini tentang {topic}",
                    "questions": [
                        {
                            "id": "q04",
                            "type": "likert",
                            "text": f"Saya setuju dengan kebijakan terkait '{topic}'",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q05",
                            "type": "likert",
                            "text": f"Topik '{topic}' akan berdampak langsung pada kehidupan saya",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q06",
                            "type": "mcq",
                            "text": f"Apa sumber utama informasi Anda tentang '{topic}'?",
                            "options": ["Media massa", "Lingkungan sosial", "Pengalaman pribadi", "Pendidikan formal", "Media sosial"],
                            "required": True
                        },
                        {
                            "id": "q07",
                            "type": "mcq",
                            "text": f"Bagaimana Anda biasanya membentuk opini tentang '{topic}'?",
                            "options": ["Mencari informasi dari berbagai sumber", "Mengandalkan opini orang terpercaya", "Intuisi pribadi", "Diskusi dengan teman/keluarga", "Tidak terlalu memikirkan"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "perilaku",
                    "title": f"Tindakan terkait {topic}",
                    "questions": [
                        {
                            "id": "q08",
                            "type": "likert",
                            "text": f"Saya bersedia mengubah pendapat tentang '{topic}' jika ada bukti baru",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q09",
                            "type": "likert",
                            "text": f"Saya aktif mendiskusikan '{topic}' dengan orang lain",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q10",
                            "type": "mcq",
                            "text": f"Apa tindakan yang paling mungkin Anda lakukan terkait '{topic}'?",
                            "options": ["Membagikan informasi", "Berdiskusi dengan orang terdekat", "Mencari tahu lebih dalam", "Tidak melakukan apa-apa", "Menulis opini di media sosial"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "refleksi",
                    "title": f"Refleksi tentang {topic}",
                    "questions": [
                        {
                            "id": "q11",
                            "type": "open",
                            "text": f"Apa pendapat pribadi Anda tentang '{topic}'? Jelaskan secara singkat.",
                            "max_length": 500,
                            "required": False
                        }
                    ]
                }
            ],
            "demographics": [
                {"id": "age", "label": "Usia", "type": "range", "required": True},
                {"id": "gender", "label": "Jenis Kelamin", "type": "choice", "options": ["Laki-laki", "Perempuan"], "required": True},
                {"id": "education", "label": "Pendidikan Terakhir", "type": "choice", "options": ["SD/SMP", "SMA/SMK", "D3", "S1", "S2/S3"], "required": True},
                {"id": "occupation", "label": "Pekerjaan", "type": "choice", "options": ["Pelajar/Mahasiswa", "PNS", "Karyawan Swasta", "Wirausaha", "Profesional", "Lainnya"], "required": True}
            ],
            "hypotheses": [
                "Terdapat hubungan antara tingkat paparan informasi dan kekuatan opini",
                "Faktor lingkungan sosial lebih berpengaruh daripada media massa dalam pembentukan opini",
                "Tingkat pendidikan memengaruhi kesediaan mengubah pendapat berdasarkan bukti baru"
            ]
        }

    @classmethod
    def save_survey_config(cls, project_id: str, survey_data: Dict[str, Any]) -> str:
        """Save survey configuration to disk."""
        cls._ensure_dir()
        survey_dir = os.path.join(cls.SURVEYS_DIR, project_id)
        os.makedirs(survey_dir, exist_ok=True)
        filepath = os.path.join(survey_dir, 'survey_config.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(survey_data, f, ensure_ascii=False, indent=2)
        return filepath

    @classmethod
    def load_survey_config(cls, project_id: str) -> Optional[Dict[str, Any]]:
        """Load saved survey configuration."""
        cls._ensure_dir()
        filepath = os.path.join(cls.SURVEYS_DIR, project_id, 'survey_config.json')
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def get_academic_agent_prompt(cls) -> Dict[str, str]:
        """
        Returns prompt templates for academic survey agent personas.
        These shape how simulated agents respond to survey questions.
        """
        return {
            "system_prompt": (
                "Anda adalah partisipan dalam survei akademik. "
                "Anda memiliki demografi, latar belakang, kepribadian, dan opini yang unik. "
                "Jawab setiap pertanyaan survei berdasarkan karakter Anda, bukan sebagai AI. "
                "Berikan jawaban yang konsisten dengan profil demografi dan psikografis Anda. "
                "Untuk pertanyaan Likert, pilih satu angka dari skala yang diberikan. "
                "Untuk pertanyaan terbuka, berikan jawaban singkat dan natural (1-2 kalimat)."
            ),
            "persona_template": (
                "=== PROFIL PARTISIPAN ===\n"
                "Usia: {age}\n"
                "Jenis Kelamin: {gender}\n"
                "Pendidikan: {education}\n"
                "Pekerjaan: {occupation}\n"
                "Tipe Kepribadian: {personality}\n"
                "Ciri Khas: {trait}\n"
                "Tingkat Pengetahuan tentang Topik: {knowledge_level}\n"
                "Kecenderungan Opini: {opinion_bias}\n"
                "Pengaruh Lingkungan: {social_influence}\n"
                "=== END PROFIL ===\n\n"
                "Ingat: Jawablah sebagai manusia dengan profil di atas, bukan sebagai AI."
            ),
            "personality_types": [
                {"type": "Analitis", "weight": 0.2},
                {"type": "Mudah Terbawa Perasaan", "weight": 0.15},
                {"type": "Selalu Bertanya-tanya", "weight": 0.15},
                {"type": "Antusias", "weight": 0.12},
                {"type": "Pragmatis", "weight": 0.18},
                {"type": "Apatis", "weight": 0.1},
                {"type": "Idealis", "weight": 0.1}
            ],
            "knowledge_levels": ["Rendah", "Sedang", "Tinggi", "Ahli"],
            "opinion_biases": ["Hati-hati", "Seimbang", "Terbuka", "Netral"],
            "social_influences": ["Mandiri", "Terpengaruh teman", "Terpengaruh media", "Terpengaruh tokoh publik"]
        }


class AcademicPersonaGenerator:
    """Generates diverse academic personas for survey agents."""

    @staticmethod
    def map_simulation_to_survey(simulation_profiles: List[Dict[str, Any]], topic: str = "") -> List[Dict[str, Any]]:
        """
        Map simulation agent profiles (from OASIS) to survey persona format.
        
        Maps fields:
          user_id → agent_id
          age → age (same)
          gender → gender (Laki-laki/Perempuan)
          mbti + education_level/knowledge_level → personality, trait
          profession → occupation
          persona + cognitive_style → opinion_bias, social_influence
          education_level → education
          iq_level, cognitive_style, knowledge_level → directly mapped (new fields)
        
        Args:
            simulation_profiles: List of agent dicts from SimulationManager.get_profiles()
            topic: The survey topic (used to infer knowledge relevance)
            
        Returns:
            List of survey persona dicts compatible with SurveyEngine.load_personas()
        """
        templates = SurveyTemplateService.get_academic_agent_prompt()
        personality_types = [p["type"] for p in templates["personality_types"]]
        
        cognitive_to_personality = {
            "Analitis": "Analitis", "Logis": "Analitis", "Praktis": "Pragmatis",
            "Intuitif": "Selalu Bertanya-tanya", "Kreatif": "Antusias",
            "Emosional": "Mudah Terbawa Perasaan", "Formal": "Pragmatis",
            "Informatif": "Analitis", "Netral": "Seimbang", "Otoritatif": "Idealis"
        }
        
        iq_to_bias = {
            "Sangat Rendah": "Hati-hati", "Rendah": "Hati-hati",
            "Rata-rata": "Netral", "Tinggi": "Terbuka", "Sangat Tinggi": "Seimbang"
        }
        
        knowledge_to_influence = {
            "Rendah": "Terpengaruh media", "Sedang": "Terpengaruh teman",
            "Tinggi": "Mandiri", "Ahli": "Mandiri"
        }
        
        def normalize_gender(g: Optional[str]) -> str:
            if not g:
                return random.choice(["Laki-laki", "Perempuan"])
            g = g.lower().strip()
            if g in ("male", "laki-laki", "laki", "pria"):
                return "Laki-laki"
            if g in ("female", "perempuan", "wanita"):
                return "Perempuan"
            return random.choice(["Laki-laki", "Perempuan"])
        
        def infer_education(prof: str, education_level: Optional[str]) -> str:
            if education_level:
                return education_level
            high_edu_occupations = ["professor", "dosen", "peneliti", "dokter", "pns", "expert"]
            if any(o in prof.lower() for o in high_edu_occupations):
                return "S2/S3"
            return random.choice(["SD/SMP", "SMA/SMK", "D3", "S1"])
        
        def infer_personality(mbti: Optional[str], cognitive: Optional[str]) -> str:
            if cognitive and cognitive in cognitive_to_personality:
                return cognitive_to_personality[cognitive]
            if mbti:
                mbti_upper = mbti.upper().strip()
                if mbti_upper.startswith("INT") or mbti_upper.startswith("ENT"):
                    return "Analitis"
                if mbti_upper.startswith("INF") or mbti_upper.startswith("ENF"):
                    return "Idealis"
                if mbti_upper.startswith("ISF") or mbti_upper.startswith("ESF"):
                    return "Antusias"
                if mbti_upper.startswith("IST") or mbti_upper.startswith("EST"):
                    return "Pragmatis"
            return random.choice(personality_types)
        
        def infer_knowledge(kl: Optional[str], topic: str) -> str:
            if kl:
                return kl
            if topic:
                return "Sedang"
            return random.choice(templates["knowledge_levels"])
        
        personas = []
        for i, profile in enumerate(simulation_profiles):
            agent_id = profile.get("user_id", profile.get("agent_id", f"agent_{i}"))
            age = profile.get("age", 30)
            gender = normalize_gender(profile.get("gender"))
            occupation = profile.get("profession") or profile.get("occupation") or ""
            education = infer_education(occupation, profile.get("education_level"))
            mbti = profile.get("mbti", "")
            cognitive = profile.get("cognitive_style", "")
            personality = infer_personality(mbti, cognitive)
            knowledge = infer_knowledge(profile.get("knowledge_level"), topic)
            iq = profile.get("iq_level", "Rata-rata")
            
            # Infer bias from IQ + cognitive style
            opinion_bias = iq_to_bias.get(iq, "Netral")
            social_influence = knowledge_to_influence.get(knowledge, "Terpengaruh teman")
            
            # Build a concise trait from the persona text
            persona_text = profile.get("persona", profile.get("bio", ""))
            trait_prefixes = {
                "Analitis": "Cenderung menganalisis sebelum merespon",
                "Mudah Terbawa Perasaan": "Emosional dan mudah terpengaruh suasana",
                "Selalu Bertanya-tanya": "Skeptis dan selalu ingin tahu lebih dalam",
                "Antusias": "Bersemangat dan ekspresif dalam berpendapat",
                "Pragmatis": "Fokus pada solusi praktis dan realistis",
                "Apatis": "Cenderung acuh dan tidak terlalu peduli",
                "Idealis": "Berpegang teguh pada prinsip dan nilai-nilai ideal",
            }
            trait = trait_prefixes.get(personality, "Memiliki pandangan unik terhadap isu sosial")
            
            persona = {
                "agent_id": f"agent_sim_{agent_id}",
                "age": age,
                "gender": gender,
                "education": education,
                "occupation": occupation if occupation else random.choice(templates["persona_template"]).split("Pekerjaan: ")[-1].split("\n")[0].strip() if "Pekerjaan: " in templates["persona_template"] else "Lainnya",
                "personality": personality,
                "trait": trait,
                "knowledge_level": knowledge,
                "opinion_bias": opinion_bias,
                "social_influence": social_influence,
                # Include original simulation fields for enrichment
                "persona_text": persona_text[:2000] if persona_text else "",
                "cognitive_style": cognitive,
                "iq_level": iq,
            }
            personas.append(persona)
        
        logger.info(f"Mapped {len(personas)} simulation profiles to survey personas")
        return personas

    @staticmethod
    def generate_batch(count: int) -> List[Dict[str, Any]]:
        """Generate a batch of diverse agent personas."""
        ages = list(range(18, 70))
        genders = ["Laki-laki", "Perempuan"]
        educations = ["SD/SMP", "SMA/SMK", "D3", "S1", "S2/S3"]
        occupations = ["Pelajar/Mahasiswa", "PNS", "Karyawan Swasta", "Wirausaha", "Profesional", "Lainnya"]
        traits = [
            "Teliti dan detail-oriented", "Cepat mengambil keputusan",
            "Cenderung ragu-ragu", "Percaya diri dan tegas",
            "Mudah dipengaruhi", "Independent dan kritis",
            "Empatik dan peduli", "Logis dan rasional",
            "Kreatif dan imajinatif", "Praktis dan efisien"
        ]
        templates = SurveyTemplateService.get_academic_agent_prompt()
        personality_types = [p["type"] for p in templates["personality_types"]]
        knowledge_levels = templates["knowledge_levels"]
        opinion_biases = templates["opinion_biases"]
        social_influences = templates["social_influences"]

        personas = []
        for i in range(count):
            persona = {
                "agent_id": f"agent_survey_{i+1:04d}",
                "age": random.choice(ages),
                "gender": random.choice(genders),
                "education": random.choice(educations),
                "occupation": random.choice(occupations),
                "personality": random.choice(personality_types),
                "trait": random.choice(traits),
                "knowledge_level": random.choice(knowledge_levels),
                "opinion_bias": random.choice(opinion_biases),
                "social_influence": random.choice(social_influences),
            }
            personas.append(persona)
        return personas
