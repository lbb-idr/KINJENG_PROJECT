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

        return {
            "title": f"Survei: {requirement[:60]}",
            "description": f"Survei akademik untuk menganalisis: {requirement}",
            "sim_type": sim_type,
            "params": params,
            "sections": [
                {
                    "id": "persepsi",
                    "title": "Persepsi dan Sikap",
                    "questions": [
                        {
                            "id": "q01",
                            "type": "likert",
                            "text": "Saya memahami isu yang diangkat dalam riset ini",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q02",
                            "type": "likert",
                            "text": "Isu ini relevan dengan kehidupan saya sehari-hari",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q03",
                            "type": "mcq",
                            "text": "Seberapa sering Anda terpapar informasi tentang topik ini?",
                            "options": ["Tidak pernah", "Jarang", "Kadang-kadang", "Sering", "Sangat sering"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "opini",
                    "title": "Opini dan Preferensi",
                    "questions": [
                        {
                            "id": "q04",
                            "type": "likert",
                            "text": "Saya memiliki opini yang kuat tentang topik ini",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q05",
                            "type": "likert",
                            "text": "Pendapat saya dipengaruhi oleh lingkungan sekitar",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q06",
                            "type": "mcq",
                            "text": "Faktor apa yang paling memengaruhi pandangan Anda?",
                            "options": ["Media massa", "Lingkungan sosial", "Pengalaman pribadi", "Pendidikan formal", "Sosial media"],
                            "required": True
                        },
                        {
                            "id": "q07",
                            "type": "mcq",
                            "text": "Bagaimana Anda biasanya membentuk opini tentang isu baru?",
                            "options": ["Mencari informasi dari berbagai sumber", "Mengandalkan opini orang terpercaya", "Intuisi pribadi", "Diskusi dengan teman/keluarga", "Tidak terlalu memikirkan"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "perilaku",
                    "title": "Perilaku dan Tindakan",
                    "questions": [
                        {
                            "id": "q08",
                            "type": "likert",
                            "text": "Saya bersedia mengubah pendapat jika ada bukti baru yang kuat",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q09",
                            "type": "likert",
                            "text": "Saya aktif mendiskusikan topik ini dengan orang lain",
                            "scale": template["scale"],
                            "labels": template["labels"],
                            "required": True
                        },
                        {
                            "id": "q10",
                            "type": "mcq",
                            "text": "Apa tindakan yang paling mungkin Anda lakukan terkait isu ini?",
                            "options": ["Membagikan informasi", "Berdiskusi dengan orang terdekat", "Mencari tahu lebih dalam", "Tidak melakukan apa-apa", "Menulis opini di media sosial"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "refleksi",
                    "title": "Refleksi Terbuka",
                    "questions": [
                        {
                            "id": "q11",
                            "type": "open",
                            "text": "Apa pendapat pribadi Anda tentang isu ini? Jelaskan secara singkat.",
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
