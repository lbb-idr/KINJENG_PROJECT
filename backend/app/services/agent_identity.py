"""
Agent Identity System — Per-Subject Cognitive Fingerprint for Multi-Agent Simulation.

INSPIRASI: TRIBE v2 (Meta FAIR)
===============================
TRIBE v2 (d'Ascoli et al., 2026) adalah multimodal foundation model yang memprediksi
aktivitas fMRI otak manusia dari stimulus video, audio, dan teks. Arsitektur kunci:
  - Feature extractors frozen: LLaMA 3.2 (text), V-JEPA2 (video), Wav2Vec-BERT (audio)
  - Unified Transformer → cortical surface projection (~20k vertices fsaverage5)
  - SubjectLayers: setiap subjek fMRI memiliki linear layer unik yang memetakan shared
    brain representation ke output spesifik subjek (per-subject readout)

Referensi:
  - Paper: d'Ascoli, Rapin, Benchetrit, Brookes, Begany, Raugel, Banville, King (2026).
    "A foundation model of vision, audition, and language for in-silico neuroscience."
    https://arxiv.org/html/2605.04326
  - GitHub: https://github.com/facebookresearch/tribev2
  - Blog: https://ai.meta.com/blog/tribe-v2-brain-predictive-foundation-model/

PENELITIAN NEUROSCIENCE (Linguistic & Cognitive Style)
======================================================
Konsep typicality dan processing_modality di sini didasarkan pada riset berikut:

1. Kepribadian → Aktivasi Otak (Personality Neuroscience)
   - Neuroticism/Harm Avoidance → lower brain typicality (respons lebih idiosinkratik)
     terhadap stimulus naturalistic yang SAMA. (Krauss et al., 2024/2025, Psychophysiology;
     bioRxiv 2024.04.23.586759)
   - Extraversion → higher typicality, especially during social stimuli
   - Cooperativeness → positive correlation with brain typicality

2. Cognitive Style → Neural Pathway (Visual vs Verbal)
   - Visualizers: aktivasi fusiform gyrus lebih kuat saat memproses deskripsi tekstual
     (mengubah teks → representasi visual mental)
   - Verbalizers: aktivasi supramarginal gyrus lebih kuat saat memproses gambar
     (mengubah gambar → representasi linguistik)
   - Kraemer et al. (2009). "The Neural Correlates of Visual and Verbal Cognitive Styles."
     https://pmc.ncbi.nlm.nih.gov/articles/PMC2697032/

3. Hierarchical Language Processing
   - Otak memprediksi linguistic units di multiple timescales: word-level DAN sentence-level
   - Sparse updating: higher-level representations hanya diupdate di sentence boundaries
   - Hierarchical linguistic predictions dan cross-level information updating selama
     narrative comprehension. (Communications Biology, 2025)
   - Fedorenko (2024). "The language network as a natural kind within the broader
     landscape of the human brain." Nature Reviews. (gwern.net)

4. Reading Experience → Neural Individuality
   - Print exposure tinggi → neural patterns LEBIH idiosinkratik selama expository reading
   - Shared reading experience → shared neural patterns di DMN (default mode network)
   - "Reading experience reveals shared and idiosyncratic neural patterns during text
     comprehension." (PMC, 2025)

5. Model-Brain Alignment (LLM + fMRI)
   - Contextual embeddings dari LLM dapat memprediksi brain responses selama naturalistic
     reading, dengan efek signifikan dari individual differences (linguistic ability,
     attentional ability, language dominance)
   - "Reading comprehension in L1 and L2 readers: neurocomputational mechanisms revealed
     through large language models." (npj Science of Learning, 2025)

IMPLEMENTASI DI KINJENG_PROJECT
================================
Setiap agen memiliki AgentIdentitySignature, analog dengan SubjectLayers di TribeV2:
  - 15+ dimensi numerik (MBTI, cognitive style, education, knowledge, IQ, opinion bias)
  - typicality: seberapa "standar" respons agen vs rata-rata grup
  - processing_modality: preferensi visual vs verbal processing
  - modulate_likert(): modulasi skor Likert berdasarkan identity (seperti SubjectLayers
    memodulasi shared representation jadi output spesifik subjek)

Identity ini di-inject ke:
  - CognitivePipeline: LLM prompt context untuk likert, open, mcq
  - InnerParliament: debat internal 5 perspektif dimodulasi identity
  - SurveyDebate: multi-agent debate posts + chairperson analysis
  - ProfileGeneration: auto-built saat OasisAgentProfile dibuat
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json

# ---- Mapping personality ke numerical dimensions ----

MBTI_DIMENSIONS = {
    'E': 1.0, 'I': -1.0,  # Ekstrover vs Introver
    'S': 1.0, 'N': -1.0,  # Sensing vs Intuisi
    'T': 1.0, 'F': -1.0,  # Thinking vs Feeling
    'J': 1.0, 'P': -1.0,  # Judging vs Perceiving
}

PROCESSING_MODALITY_MAP = {
    'Analitis': 0.0,   # verbal
    'Intuitif': 0.7,   # visual
    'Praktis':  0.3,   # balanced
    'Kreatif':  0.8,   # visual
    'Logis':    0.0,   # verbal
    'Emosional': 0.5,  # balanced
}

# Typicality: seberapa 'standar' respons agen vs rata-rata grup.
# Terinspirasi dari penelitian: Neuroticism → lower brain typicality,
# Extraversion → higher typicality during social stimuli
TYPICALITY_TRAIT_MODIFIERS = {
    'Suka Menganalisis': 0.4,
    'Mudah Terbawa Perasaan': -0.3,
    'Selalu Bertanya-tanya': -0.2,
    'Semangat': 0.3,
    'Praktis': 0.5,
    'Cuek': -0.4,
    'Ideal': -0.1,
}

COGNITIVE_STYLE_MAP = {
    'Analitis': {'analytical': 1.0, 'creative': -0.3, 'emotional': -0.5, 'practical': 0.2, 'systematic': 0.8},
    'Intuitif': {'analytical': -0.4, 'creative': 0.9, 'emotional': 0.3, 'practical': -0.2, 'systematic': -0.6},
    'Praktis':  {'analytical': 0.3, 'creative': -0.2, 'emotional': -0.4, 'practical': 1.0, 'systematic': 0.5},
    'Kreatif':  {'analytical': -0.3, 'creative': 1.0, 'emotional': 0.5, 'practical': -0.3, 'systematic': -0.5},
    'Logis':    {'analytical': 1.0, 'creative': -0.1, 'emotional': -0.6, 'practical': 0.4, 'systematic': 0.9},
    'Emosional': {'analytical': -0.5, 'creative': 0.4, 'emotional': 1.0, 'practical': -0.1, 'systematic': -0.4},
}

EDUCATION_LEVEL_MAP = {
    'SD/SMP': 0.1,
    'SMA/SMK': 0.3,
    'D3': 0.5,
    'S1': 0.7,
    'S2': 0.85,
    'S3': 1.0,
}

KNOWLEDGE_LEVEL_MAP = {
    'Rendah': 0.2,
    'Sedang': 0.5,
    'Tinggi': 0.8,
    'Ahli': 1.0,
}

IQ_LEVEL_MAP = {
    'Sangat Rendah': 0.1,
    'Rendah': 0.3,
    'Rata-rata': 0.5,
    'Tinggi': 0.8,
    'Sangat Tinggi': 1.0,
}

OPINION_BIAS_MAP = {
    'sangat setuju': 0.9, 'sangat mendukung': 0.9,
    'setuju': 0.6, 'mendukung': 0.7,
    'netral': 0.0, 'seimbang': 0.0,
    'tidak setuju': -0.6, 'sangat tidak setuju': -0.9,
    'kritis': -0.7, 'sangat kritis': -0.9,
    'hati-hati': -0.3,
    'terbuka': 0.5, 'optimis': 0.5,
}


@dataclass
class AgentIdentitySignature:
    """
    Signature kognitif unik per agen — analog dengan SubjectLayers di TribeV2.
    
    Berbeda dengan profil statis (nama, usia, dll), signature ini adalah vektor
    numerik yang secara konsisten memodulasi bagaimana agen memproses informasi
    dan merespons stimulus di semua konteks.
    """
    # MBTI-derived dimensions
    extroversion: float = 0.0      # E=1.0, I=-1.0
    sensing: float = 0.0           # S=1.0, N=-1.0
    thinking: float = 0.0          # T=1.0, F=-1.0
    judging: float = 0.0           # J=1.0, P=-1.0

    # Cognitive style dimensions
    analytical: float = 0.0
    creative: float = 0.0
    emotional: float = 0.0
    practical: float = 0.0
    systematic: float = 0.0

    # Capacity dimensions
    education_factor: float = 0.5
    knowledge_factor: float = 0.5
    iq_factor: float = 0.5

    # Disposition
    opinion_bias: float = 0.0     # -1.0 (sangat negatif) to 1.0 (sangat positif)
    openness: float = 0.0         # derived from personality
    
    # Demographics
    age_group: str = 'dewasa'
    gender_code: float = 0.0      # male=0.0, female=0.5, other=0.25
    
    # Brain response modulation (dari neuroscience findings)
    typicality: float = 0.5       # 0.0=sangat idiosinkratik, 1.0=sangat typical
    processing_modality: float = 0.3  # 0.0=verbal, 1.0=visual
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'extroversion': self.extroversion,
            'sensing': self.sensing,
            'thinking': self.thinking,
            'judging': self.judging,
            'analytical': self.analytical,
            'creative': self.creative,
            'emotional': self.emotional,
            'practical': self.practical,
            'systematic': self.systematic,
            'education_factor': self.education_factor,
            'knowledge_factor': self.knowledge_factor,
            'iq_factor': self.iq_factor,
            'opinion_bias': self.opinion_bias,
            'openness': self.openness,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    def modulate_likert(self, base_score: int, scale: int = 5) -> int:
        """
        Modulasi skor Likert berdasarkan identitas agen.
        
        Terinspirasi dari TribeV2 SubjectLayers: shared representation (base_score)
        dimodulasi oleh subject-specific layer (identity signature) untuk menghasilkan
        output yang unik per subjek/agen.
        
        Faktor modulasi:
        - opinion_bias: ±1 dari skor dasar
        - openness: agen dengan openness rendah cenderung ke tengah
        - thinking/feeling: thinking agents lebih konservatif, feeling lebih variatif
        """
        delta = 0
        
        # Opinion bias: menggeser skor
        if self.opinion_bias > 0.3:
            delta += 1
        elif self.opinion_bias < -0.3:
            delta -= 1
        
        # Openness: agen tertutup cenderung ke tengah
        if self.openness < 0.3:
            mid = (scale + 1) / 2
            if abs(base_score - mid) > 1:
                delta += -1 if base_score > mid else 1
        
        # Education/knowledge: agen berpengetahuan lebih percaya diri (variasi lebih besar)
        knowledge_conf = (self.education_factor + self.knowledge_factor + self.iq_factor) / 3
        if knowledge_conf > 0.7 and base_score > scale // 2:
            delta += 1
        elif knowledge_conf < 0.3:
            delta += -1 if base_score > scale // 2 else 1
        
        return max(1, min(scale, base_score + delta))


class AgentIdentityEngine:
    """
    Engine yang mengelola identitas kognitif semua agen.
    
    Terinspirasi dari TribeV2 di mana setiap subjek fMRI punya SubjectLayers:
    - Shared representation (pengetahuan umum LLM) + Subject-specific readout (identitas agen)
    - Modulasi konsisten di semua modalitas input
    
    Di sini: setiap agen punya AgentIdentitySignature yang memodulasi bagaimana
    mereka memproses pertanyaan, berdebat, dan merespons secara konsisten.
    """
    
    def __init__(self):
        self._signatures: Dict[str, AgentIdentitySignature] = {}
    
    def build_signature(self, agent_id: str, profile_data: Dict[str, Any]) -> AgentIdentitySignature:
        """
        Membangun AgentIdentitySignature dari data profil agen.
        
        Analog dengan TribeV2 SubjectLayers.build() yang membuat linear layer
        per subjek dari data anatomi otak mereka.
        """
        sig = AgentIdentitySignature()
        
        # 1. MBTI → 4 dimensions
        mbti = profile_data.get('mbti', 'INTJ').upper()
        for i, dim in enumerate([('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]):
            if len(mbti) > i:
                letter = mbti[i]
                if letter == dim[0]:
                    getattr(sig, ['extroversion', 'sensing', 'thinking', 'judging'][i])
                    setattr(sig, ['extroversion', 'sensing', 'thinking', 'judging'][i], 1.0)
                elif letter == dim[1]:
                    setattr(sig, ['extroversion', 'sensing', 'thinking', 'judging'][i], -1.0)
        
        # 2. Cognitive style
        cognitive_style = profile_data.get('cognitive_style', 'Logis')
        if cognitive_style in COGNITIVE_STYLE_MAP:
            for k, v in COGNITIVE_STYLE_MAP[cognitive_style].items():
                setattr(sig, k, v)
        
        # 3. Education
        education = profile_data.get('education_level', 'SMA/SMK')
        if isinstance(education, str) and education in EDUCATION_LEVEL_MAP:
            sig.education_factor = EDUCATION_LEVEL_MAP[education]
        elif isinstance(education, (int, float)):
            sig.education_factor = min(1.0, max(0.0, float(education) / 5.0))
        
        # 4. Knowledge
        knowledge = profile_data.get('knowledge_level', 'Sedang')
        if knowledge in KNOWLEDGE_LEVEL_MAP:
            sig.knowledge_factor = KNOWLEDGE_LEVEL_MAP[knowledge]
        
        # 5. IQ
        iq = profile_data.get('iq_level', 'Rata-rata')
        if iq in IQ_LEVEL_MAP:
            sig.iq_factor = IQ_LEVEL_MAP[iq]
        
        # 6. Opinion bias (case-insensitive)
        opinion_bias = profile_data.get('opinion_bias', 'netral')
        if isinstance(opinion_bias, str):
            bias_lower = opinion_bias.lower()
            # Find matching key in OPINION_BIAS_MAP (case-insensitive)
            matched = None
            for key, val in OPINION_BIAS_MAP.items():
                if bias_lower == key.lower() or bias_lower.startswith(key.lower()):
                    matched = val
                    break
            sig.opinion_bias = matched if matched is not None else 0.0
        elif isinstance(opinion_bias, (int, float)):
            sig.opinion_bias = max(-1.0, min(1.0, float(opinion_bias)))
        
        # 7. Openness (derived)
        openness = 0.3  # default
        if isinstance(opinion_bias, str):
            bias_lower = opinion_bias.lower()
            if bias_lower in ['terbuka', 'sangat setuju', 'sangat mendukung', 'optimis']:
                openness = 0.8
            elif bias_lower in ['hati-hati', 'kritis', 'sangat kritis', 'sangat tidak setuju']:
                openness = 0.2
        sig.openness = openness
        
        # 8. Age group
        age = profile_data.get('age', 30)
        if age is not None:
            if age < 18:
                sig.age_group = 'remaja'
            elif age < 35:
                sig.age_group = 'dewasa_muda'
            elif age < 55:
                sig.age_group = 'dewasa'
            else:
                sig.age_group = 'senior'
        
        # 9. Gender code
        gender = profile_data.get('gender', 'other')
        sig.gender_code = {'male': 0.0, 'female': 0.5, 'other': 0.25}.get(gender, 0.25)
        
        # 10. Typicality (derived from personality + cognitive style)
        # Neuroscience: Neuroticism → lower typicality, Extraversion → higher
        personality = profile_data.get('personality', 'Praktis')
        typicality_base = TYPICALITY_TRAIT_MODIFIERS.get(personality, 0.0)
        sig.typicality = max(0.0, min(1.0, 0.5 + typicality_base))
        
        # 11. Processing modality (derived from cognitive style)
        # Neuroscience: Visualizers use fusiform gyrus, Verbalizers use supramarginal gyrus
        cognitive_style = profile_data.get('cognitive_style', 'Logis')
        sig.processing_modality = PROCESSING_MODALITY_MAP.get(cognitive_style, 0.3)
        
        self._signatures[agent_id] = sig
        return sig
    
    def get_signature(self, agent_id: str) -> Optional[AgentIdentitySignature]:
        return self._signatures.get(agent_id)
    
    def build_prompt_context(self, agent_id: str) -> str:
        """
        Menghasilkan konteks identitas untuk disisipkan ke prompt LLM.
        
        Ini adalah 'identity layer prompt' — analog dengan bagaimana SubjectLayers
        di TribeV2 memodulasi representasi bersama menjadi output spesifik subjek.
        """
        sig = self._signatures.get(agent_id)
        if not sig:
            return ''
        
        traits = []
        
        # Ekstrover/Introver
        if sig.extroversion > 0:
            traits.append('Anda adalah pribadi yang ekstrover dan ekspresif')
        elif sig.extroversion < 0:
            traits.append('Anda adalah pribadi yang introver dan reflektif')
        
        # Thinking/Feeling
        if sig.thinking > 0:
            traits.append('Anda cenderung berpikir logis dan objektif')
        elif sig.thinking < 0:
            traits.append('Anda cenderung menggunakan perasaan dan empati')
        
        # Cognitive style
        if sig.analytical > 0.5:
            traits.append('Anda sangat analitis dalam memproses informasi')
        if sig.creative > 0.5:
            traits.append('Anda memiliki cara berpikir yang kreatif dan out-of-the-box')
        if sig.emotional > 0.5:
            traits.append('Anda sangat dipengaruhi oleh emosi dalam mengambil keputusan')
        if sig.practical > 0.5:
            traits.append('Anda praktis dan fokus pada solusi nyata')
        
        # Knowledge & education
        if sig.knowledge_factor > 0.7:
            traits.append('Anda memiliki pengetahuan yang mendalam tentang topik ini')
        elif sig.knowledge_factor < 0.3:
            traits.append('Pengetahuan Anda tentang topik ini terbatas')
        
        if sig.opinion_bias > 0.3:
            traits.append('Anda cenderung mendukung dan optimis terhadap isu ini')
        elif sig.opinion_bias < -0.3:
            traits.append('Anda cenderung kritis dan skeptis terhadap isu ini')
        
        if sig.age_group == 'remaja':
            traits.append('Anda masih muda dan memiliki perspektif yang segar')
        elif sig.age_group == 'senior':
            traits.append('Anda memiliki banyak pengalaman hidup')
        
        if not traits:
            traits.append('Anda memiliki perspektif yang seimbang dan netral')
        
        return '\n'.join(['[IDENTITAS KOGNITIF]'] + traits + ['[/IDENTITAS KOGNITIF]'])


# Singleton
_identity_engine: Optional[AgentIdentityEngine] = None


def get_identity_engine() -> AgentIdentityEngine:
    global _identity_engine
    if _identity_engine is None:
        _identity_engine = AgentIdentityEngine()
    return _identity_engine


def build_agent_identity(agent_id: str, profile_data: Dict[str, Any]) -> AgentIdentitySignature:
    """Build dan daftarkan identitas agen. Panggil saat profil agen dibuat."""
    engine = get_identity_engine()
    return engine.build_signature(agent_id, profile_data)


def get_identity_context(agent_id: str) -> str:
    """Dapatkan konteks identitas untuk prompt LLM."""
    engine = get_identity_engine()
    return engine.build_prompt_context(agent_id)


def get_signature(agent_id: str) -> Optional[AgentIdentitySignature]:
    """Dapatkan signature agen."""
    return get_identity_engine().get_signature(agent_id)
