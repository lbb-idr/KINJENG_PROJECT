"""
Survey Statistics — Descriptive and inferential statistics for survey results.
"""

import math
import statistics
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict

from ..utils.logger import get_logger

logger = get_logger('mirofish.survey.stats')


class SurveyStatistics:
    """
    Compute descriptive and inferential statistics from survey results.
    
    Capabilities:
    - Descriptive stats (mean, median, mode, std, variance, distribution)
    - Frequency distributions for MCQ questions
    - Cross-tabulations (demographic × likert)
    - Cronbach's alpha (internal consistency)
    - Confidence intervals
    """

    @staticmethod
    def compute_all(results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute all statistics from survey engine results.
        
        Args:
            results: Output from SurveyEngine.run_survey()
            
        Returns:
            Statistics object with descriptive, frequencies, cross-tabs, etc.
        """
        agents = results.get('results', [])
        if not agents:
            return {"error": "No results to analyze"}

        questions = SurveyStatistics._extract_questions(agents)
        likert_scale = results.get('likert_scale', 5)

        descriptives = {}
        frequencies = {}
        cross_tabs = []
        all_likert_scores = {}

        for q_id, q_data in questions.items():
            q_type = q_data['type']

            if q_type == 'likert':
                scores = q_data['scores']
                if scores:
                    desc = SurveyStatistics._descriptive(scores, likert_scale)
                    desc['question_text'] = q_data['text']
                    descriptives[q_id] = desc

                    freq = SurveyStatistics._frequency_distribution(scores, likert_scale)
                    freq['question_text'] = q_data['text']
                    frequencies[q_id] = freq
                    all_likert_scores[q_id] = scores

            elif q_type == 'mcq':
                answers = q_data['answers']
                freq = SurveyStatistics._mcq_frequency(answers)
                freq['question_text'] = q_data['text']
                frequencies[q_id] = freq

            elif q_type == 'open':
                answers = q_data['answers']
                frequencies[q_id] = {
                    "type": "open",
                    "question_text": q_data['text'],
                    "total_responses": len(answers),
                    "responses": answers[:10]
                }

        alpha = None
        if len(all_likert_scores) >= 2:
            try:
                alpha = SurveyStatistics._cronbach_alpha(list(all_likert_scores.values()))
            except Exception as e:
                logger.warning(f"Cronbach's alpha computation failed: {e}")

        demo_cross = SurveyStatistics._demographic_cross_tabs(agents, list(descriptives.keys()))

        return {
            "likert_scale": likert_scale,
            "total_respondents": results.get('total_agents', len(agents)),
            "total_questions": results.get('total_questions', len(questions)),
            "descriptives": descriptives,
            "frequencies": frequencies,
            "cronbach_alpha": alpha,
            "cross_tabs": demo_cross,
            "summary": SurveyStatistics._generate_summary(descriptives, alpha, likert_scale)
        }

    @staticmethod
    def _extract_questions(agents: List[Dict]) -> Dict[str, Dict]:
        """Extract question data across all agents."""
        questions = {}
        for agent in agents:
            for resp in agent.get('responses', []):
                q_id = resp.get('question_id', 'unknown')
                if q_id not in questions:
                    questions[q_id] = {
                        'type': 'likert',
                        'text': resp.get('question', ''),
                        'scores': [],
                        'answers': []
                    }
                questions[q_id]['answers'].append(resp.get('answer', ''))
                if resp.get('likert_score') is not None:
                    questions[q_id]['type'] = 'likert'
                    questions[q_id]['scores'].append(resp['likert_score'])

        for q_id, q_data in questions.items():
            if q_data['scores']:
                q_data['type'] = 'likert'
            else:
                non_empty = [a for a in q_data['answers'] if a]
                if non_empty:
                    if any(len(a) > 50 for a in non_empty):
                        q_data['type'] = 'open'
                    else:
                        q_data['type'] = 'mcq'
        return questions

    @staticmethod
    def _descriptive(scores: List[int], scale: int) -> Dict[str, Any]:
        n = len(scores)
        if n == 0:
            return {"error": "No data"}
        mean = statistics.mean(scores)
        median = statistics.median(scores)
        try:
            mode = statistics.mode(scores)
        except statistics.StatisticsError:
            mode = Counter(scores).most_common(1)[0][0]
        variance = statistics.variance(scores) if n > 1 else 0.0
        std_dev = math.sqrt(variance)
        margin = 1.96 * std_dev / math.sqrt(n)
        return {
            "n": n,
            "mean": round(mean, 3),
            "median": median,
            "mode": mode,
            "variance": round(variance, 3),
            "std_dev": round(std_dev, 3),
            "min": min(scores),
            "max": max(scores),
            "range": max(scores) - min(scores),
            "confidence_95": round(margin, 3),
            "ci_lower": round(mean - margin, 3),
            "ci_upper": round(mean + margin, 3),
            "relative_mean": round((mean - 1) / (scale - 1) * 100, 1)
        }

    @staticmethod
    def _frequency_distribution(scores: List[int], scale: int) -> Dict[str, Any]:
        counter = Counter(scores)
        total = len(scores)
        dist = {}
        for i in range(1, scale + 1):
            count = counter.get(i, 0)
            dist[str(i)] = {
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0
            }
        return {
            "type": "likert",
            "distribution": dist,
            "total": total
        }

    @staticmethod
    def _mcq_frequency(answers: List[str]) -> Dict[str, Any]:
        counter = Counter(answers)
        total = len(answers)
        dist = {}
        for opt, count in counter.most_common():
            dist[opt] = {
                "count": count,
                "percentage": round(count / total * 100, 1) if total > 0 else 0
            }
        return {
            "type": "mcq",
            "distribution": dist,
            "total": total
        }

    @staticmethod
    def _cronbach_alpha(score_lists: List[List[int]]) -> float:
        """Compute Cronbach's alpha for internal consistency."""
        k = len(score_lists)
        if k < 2:
            return 0.0
        min_len = min(len(s) for s in score_lists)
        if min_len < 2:
            return 0.0
        trimmed = [s[:min_len] for s in score_lists]
        item_variances = [statistics.variance(item) for item in trimmed]
        total_scores = [sum(trimmed[i][j] for i in range(k)) for j in range(min_len)]
        total_variance = statistics.variance(total_scores)
        sum_item_var = sum(item_variances)
        if total_variance <= 0:
            return 0.0
        alpha = (k / (k - 1)) * (1 - sum_item_var / total_variance)
        return round(alpha, 3)

    @staticmethod
    def _demographic_cross_tabs(
        agents: List[Dict],
        likert_question_ids: List[str]
    ) -> List[Dict]:
        """Compute cross-tabulations of demographics vs likert questions."""
        if not likert_question_ids:
            return []

        cross_tabs = []
        demo_fields = ['age', 'gender', 'education', 'occupation', 'personality']

        for field in demo_fields:
            groups = defaultdict(list)
            for agent in agents:
                persona = agent.get('persona', {})
                val = str(persona.get(field, 'unknown'))
                for resp in agent.get('responses', []):
                    q_id = resp.get('question_id')
                    score = resp.get('likert_score')
                    if q_id in likert_question_ids and score is not None:
                        groups[val].append(score)

            if len(groups) < 2:
                continue

            tab_data = []
            for group_name, scores in sorted(groups.items()):
                if scores:
                    tab_data.append({
                        "group": group_name,
                        "n": len(scores),
                        "mean": round(statistics.mean(scores), 2),
                        "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0
                    })

            if len(tab_data) >= 2:
                cross_tabs.append({
                    "field": field,
                    "groups": tab_data
                })

        return cross_tabs

    @staticmethod
    def _generate_summary(
        descriptives: Dict[str, Any],
        alpha: Optional[float],
        scale: int
    ) -> Dict[str, Any]:
        """Generate a plain-language summary of the statistics."""
        if not descriptives:
            return {"text": "Tidak cukup data untuk analisis."}

        means = [d['mean'] for d in descriptives.values() if 'mean' in d]
        if not means:
            return {"text": "Tidak ada data Likert untuk dianalisis."}

        overall_mean = statistics.mean(means)
        overall_std = statistics.stdev(means) if len(means) > 1 else 0

        rel_mean = (overall_mean - 1) / (scale - 1) * 100
        if rel_mean > 60:
            tendency = "cenderung SETUJU"
        elif rel_mean < 40:
            tendency = "cenderung TIDAK SETUJU"
        else:
            tendency = "cenderung NETRAL"

        consistency = ""
        if alpha is not None:
            if alpha >= 0.7:
                consistency = f"Konsistensi internal tinggi (α={alpha:.3f})"
            elif alpha >= 0.5:
                consistency = f"Konsistensi internal sedang (α={alpha:.3f})"
            else:
                consistency = f"Konsistensi internal rendah (α={alpha:.3f})"

        variability = "rendah" if overall_std < 1.0 else "sedang" if overall_std < 1.5 else "tinggi"

        return {
            "text": (
                f"Rata-rata skor Likert: {overall_mean:.2f}/{scale} ({rel_mean:.1f}% dari skala), "
                f"{tendency}. Variabilitas jawaban {variability} (SD={overall_std:.2f}). "
                f"{consistency}."
            ),
            "overall_mean": round(overall_mean, 3),
            "overall_std": round(overall_std, 3),
            "overall_relative_mean": round(rel_mean, 1),
            "tendency": tendency,
            "variability": variability,
            "cronbach_alpha": alpha,
            "total_questions_analyzed": len(descriptives)
        }
