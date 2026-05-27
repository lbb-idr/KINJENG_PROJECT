"""
Survey Generator — LLM-powered academic survey generation with document context.
"""

import json
import os
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.survey.generator')


SIM_TYPE_PROMPTS = {
    "academic": (
        "Buat survei untuk riset akademik. Fokus pada skala Likert, konstruk teoritis, "
        "dan validitas internal. Gunakan bahasa formal akademik."
    ),
    "political": (
        "Buat kuesioner polling politik. Fokus pada preferensi kandidat, isu kebijakan, "
        "identitas partai, dan swing analysis. Gunakan bahasa netral."
    ),
    "market": (
        "Buat survei riset pasar. Fokus pada perilaku konsumen, brand perception, NPS, "
        "dan preferensi produk. Gunakan bahasa yang mudah dipahami."
    ),
    "social": (
        "Buat simulasi opini publik. Fokus pada isu sosial, respons emosional, "
        "pengaruh lingkungan, dan dinamika kelompok."
    ),
    "custom": (
        "Buat survei berdasarkan kebutuhan khusus. Ikuti deskripsi dan persyaratan "
        "yang diberikan pengguna."
    )
}


class SurveyGenerator:
    """
    Generates academic-quality survey configurations using LLM,
    optionally incorporating uploaded document content.
    """

    @classmethod
    def generate(
        cls,
        requirement: str,
        sim_type: str,
        params: Dict[str, Any],
        document_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete survey using LLM.
        
        Args:
            requirement: Natural language requirement
            sim_type: Type of simulation
            params: Survey parameters (agentCount, likertScale, etc.)
            document_context: Optional extracted text from uploaded documents
            
        Returns:
            Complete survey configuration
        """
        scale = params.get('likertScale', 5)
        agent_count = params.get('agentCount', 500)
        sim_prompt = SIM_TYPE_PROMPTS.get(sim_type, SIM_TYPE_PROMPTS["custom"])

        likert_labels_5 = "1=Sangat Tidak Setuju, 2=Tidak Setuju, 3=Netral, 4=Setuju, 5=Sangat Setuju"
        likert_labels_7 = "1=STS, 2=TS, 3=ATS, 4=N, 5=AS, 6=S, 7=SS"
        labels = likert_labels_7 if scale == 7 else likert_labels_5

        doc_section = ""
        if document_context:
            doc_section = f"\n\nDokumen referensi:\n{document_context[:3000]}"

        system_prompt = f"""Anda adalah ahli metodologi survei akademik. Buat rancangan survei berdasarkan spesifikasi berikut.

{sim_prompt}
Skala Likert: {scale}-point ({labels})
Target responden: {agent_count} partisipan{doc_section}

Kebutuhan riset: {requirement}

Output JSON WAJIB dengan struktur berikut (jangan tambah field lain di luar struktur ini):
{{
  "title": "Judul Survei",
  "description": "Deskripsi singkat 2-3 kalimat",
  "introduction": "Paragraf pengantar untuk responden",
  "sim_type": "{sim_type}",
  "sections": [
    {{
      "id": "section_1",
      "title": "Nama Section",
      "description": "Instruksi singkat untuk section ini",
      "questions": [
        {{
          "id": "q01",
          "type": "likert",
          "text": "Teks pertanyaan",
          "scale": [1,2,3,4,5],
          "labels": ["label1","label2","label3","label4","label5"]
        }}
      ]
    }}
  ],
  "demographics": [
    {{
      "id": "age",
      "label": "Usia",
      "type": "range",
      "required": true
    }}
  ],
  "hypotheses": ["Hipotesis 1", "Hipotesis 2", "Hipotesis 3"]
}}

PEDOMAN:
1. Minimal 3 section, 10 pertanyaan inti
2. CAMPURAN tipe: likert (60%), mcq (20%), open-ended (20%)
3. Setiap section punya 3-5 pertanyaan
4. Pertanyaan mcq WAJIB punya field "options" (array string)
5. Pertanyaan open WAJIB punya field "max_length" (number)
6. Gunakan bahasa Indonesia yang baik dan benar
7. PENTING: Setiap pertanyaan WAJIB menyebut topik riset secara eksplisit, jangan pakai kata "ini", "tersebut", atau "topik ini". Contoh: alih-alih "Apakah Anda setuju dengan kebijakan ini?", tulis "Apakah Anda setuju dengan kebijakan kenaikan PPN 12%?"
8. Ikuti kaidah metodologi survei akademik"""

        try:
            llm = LLMClient(temperature=0.7, max_tokens=4096)
            response = llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Buat survei spesifik tentang '{requirement}'. Setiap pertanyaan harus menyebut topik ini secara langsung, jangan pakai kata ganti 'ini' atau 'tersebut'."}
                ],
                response_format={"type": "json_object"}
            )

            survey = json.loads(response)
            survey['sim_type'] = sim_type
            survey['params'] = params
            survey['generated_by'] = 'llm'
            cls._validate_survey(survey)
            return survey

        except Exception as e:
            logger.error(f"LLM survey generation failed: {e}")
            logger.info("Falling back to template-based survey")
            from .survey_service import SurveyTemplateService
            fallback = SurveyTemplateService._fallback_survey(requirement, sim_type, params)
            fallback['generated_by'] = 'template_fallback'
            return fallback

    @classmethod
    def _validate_survey(cls, survey: Dict[str, Any]):
        """Ensure the survey has the required structure."""
        if 'sections' not in survey or not survey['sections']:
            survey['sections'] = [{
                "id": "utama",
                "title": "Pertanyaan Utama",
                "description": "Jawablah pertanyaan berikut dengan jujur.",
                "questions": []
            }]
        if 'demographics' not in survey:
            survey['demographics'] = []
        if 'hypotheses' not in survey:
            survey['hypotheses'] = []
        if 'introduction' not in survey:
            survey['introduction'] = f"Terima kasih telah berpartisipasi dalam survei ini."

        for section in survey['sections']:
            for q in section.get('questions', []):
                if q.get('type') == 'mcq' and 'options' not in q:
                    q['options'] = ["Pilihan 1", "Pilihan 2", "Pilihan 3"]
                if q.get('type') == 'open' and 'max_length' not in q:
                    q['max_length'] = 500
                if q.get('type') == 'likert':
                    if 'scale' not in q:
                        q['scale'] = [1, 2, 3, 4, 5]
                    if 'labels' not in q:
                        q['labels'] = ["STS", "TS", "N", "S", "SS"]

    @classmethod
    def enhance_existing(cls, survey: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """Use LLM to enhance an existing survey based on feedback."""
        survey_json = json.dumps(survey, ensure_ascii=False)[:4000]

        try:
            llm = LLMClient(temperature=0.6)
            response = llm.chat(
                messages=[
                    {"role": "system", "content": "Anda adalah ahli metodologi survei yang menyempurnakan rancangan survei."},
                    {"role": "user", "content": (
                        f"Survey existing:\n{survey_json}\n\n"
                        f"Feedback/permintaan revisi:\n{feedback}\n\n"
                        f"Kembalikan JSON survei yang sudah disempurnakan. "
                        f"Pertahankan struktur yang sama."
                    )}
                ],
                response_format={"type": "json_object"}
            )

            enhanced = json.loads(response)
            enhanced['params'] = survey.get('params')
            enhanced['sim_type'] = survey.get('sim_type')
            cls._validate_survey(enhanced)
            return enhanced

        except Exception as e:
            logger.error(f"Survey enhancement failed: {e}")
            return survey


class SurveyResultStore:
    """Persists and retrieves completed survey results."""

    RESULTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'survey_results')

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.RESULTS_DIR, exist_ok=True)

    @classmethod
    def save(cls, project_id: str, results: Dict[str, Any]) -> str:
        cls._ensure_dir()
        result_dir = os.path.join(cls.RESULTS_DIR, project_id)
        os.makedirs(result_dir, exist_ok=True)
        path = os.path.join(result_dir, 'results.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, project_id: str) -> Optional[Dict[str, Any]]:
        cls._ensure_dir()
        path = os.path.join(cls.RESULTS_DIR, project_id, 'results.json')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @classmethod
    def list(cls) -> List[str]:
        cls._ensure_dir()
        return [d for d in os.listdir(cls.RESULTS_DIR)
                if os.path.isdir(os.path.join(cls.RESULTS_DIR, d))]

    @classmethod
    def delete(cls, project_id: str) -> bool:
        import shutil
        result_dir = os.path.join(cls.RESULTS_DIR, project_id)
        if not os.path.exists(result_dir):
            return False
        shutil.rmtree(result_dir)
        return True
