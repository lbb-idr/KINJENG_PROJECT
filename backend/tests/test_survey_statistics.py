"""Tests for SurveyStatistics."""
import math
import pytest
from app.services.survey_statistics import SurveyStatistics


class TestDescriptiveStats:
    def test_mean_median_mode_known_values(self):
        scores = [2, 3, 3, 4, 5]
        result = SurveyStatistics._descriptive(scores, 5)
        assert result["n"] == 5
        assert result["mean"] == pytest.approx(3.4, rel=1e-3)
        assert result["median"] == 3
        assert result["mode"] == 3
        assert result["min"] == 2
        assert result["max"] == 5
        assert result["range"] == 3

    def test_variance_and_std(self):
        scores = [1, 1, 1, 5, 5, 5]
        result = SurveyStatistics._descriptive(scores, 5)
        assert result["variance"] == pytest.approx(4.8, rel=1e-2)
        assert result["std_dev"] == pytest.approx(math.sqrt(4.8), rel=1e-2)

    def test_confidence_interval(self):
        scores = [3, 3, 3, 3, 3]
        result = SurveyStatistics._descriptive(scores, 5)
        assert result["ci_lower"] == 3.0
        assert result["ci_upper"] == 3.0

    def test_relative_mean(self):
        scores = [5, 5, 5, 5]
        result = SurveyStatistics._descriptive(scores, 5)
        assert result["relative_mean"] == 100.0

        scores = [1, 1, 1, 1]
        result = SurveyStatistics._descriptive(scores, 5)
        assert result["relative_mean"] == 0.0

    def test_empty_scores(self):
        result = SurveyStatistics._descriptive([], 5)
        assert "error" in result

    def test_mode_fallback_when_no_unique_mode(self):
        scores = [1, 1, 2, 2, 3]
        result = SurveyStatistics._descriptive(scores, 5)
        assert result["mode"] in (1, 2)


class TestFrequencyDistribution:
    def test_likert_frequency(self):
        scores = [1, 2, 2, 3, 3, 3, 4, 4, 5]
        result = SurveyStatistics._frequency_distribution(scores, 5)
        assert result["total"] == 9
        assert result["distribution"]["1"]["count"] == 1
        assert result["distribution"]["2"]["count"] == 2
        assert result["distribution"]["3"]["count"] == 3
        assert result["distribution"]["4"]["count"] == 2
        assert result["distribution"]["5"]["count"] == 1

    def test_frequency_percentages_sum_to_100(self):
        scores = [1, 2, 3, 4, 5]
        result = SurveyStatistics._frequency_distribution(scores, 5)
        total_pct = sum(v["percentage"] for v in result["distribution"].values())
        assert total_pct == pytest.approx(100.0, rel=0.1)

    def test_empty_frequency(self):
        result = SurveyStatistics._frequency_distribution([], 5)
        assert result["total"] == 0


class TestMCQFrequency:
    def test_mcq_distribution(self):
        answers = ["A", "B", "A", "C", "B", "A"]
        result = SurveyStatistics._mcq_frequency(answers)
        assert result["total"] == 6
        assert result["distribution"]["A"]["count"] == 3
        assert result["distribution"]["B"]["count"] == 2
        assert result["distribution"]["C"]["count"] == 1

    def test_mcq_empty(self):
        result = SurveyStatistics._mcq_frequency([])
        assert result["total"] == 0


class TestCronbachAlpha:
    def test_perfect_consistency(self):
        """All respondents answer identically across items — no variance means alpha is undefined."""
        scores = [
            [3, 3, 3],
            [3, 3, 3],
            [3, 3, 3],
        ]
        alpha = SurveyStatistics._cronbach_alpha(scores)
        assert alpha == 0.0

    def test_high_consistency(self):
        """Known value: if all items correlate perfectly."""
        scores = [
            [4, 5, 4, 5],
            [3, 4, 3, 4],
            [2, 3, 2, 3],
        ]
        alpha = SurveyStatistics._cronbach_alpha(scores)
        assert alpha >= 0.7

    def test_low_consistency(self):
        """Random unrelated scores produce low alpha."""
        scores = [
            [1, 5, 1, 5],
            [5, 1, 5, 1],
        ]
        alpha = SurveyStatistics._cronbach_alpha(scores)
        assert alpha < 0.5 or alpha == pytest.approx(0.0, abs=0.01)

    def test_insufficient_items(self):
        assert SurveyStatistics._cronbach_alpha([[1, 2]]) == 0.0
        assert SurveyStatistics._cronbach_alpha([]) == 0.0

    def test_single_respondent(self):
        scores = [[1], [2]]
        assert SurveyStatistics._cronbach_alpha(scores) == 0.0


class TestCrossTabs:
    def test_cross_tabulation(self):
        agents = [
            {
                "persona": {"age": "young"},
                "responses": [
                    {"question_id": "q1", "likert_score": 4},
                    {"question_id": "q2", "likert_score": 3},
                ],
            },
            {
                "persona": {"age": "old"},
                "responses": [
                    {"question_id": "q1", "likert_score": 2},
                    {"question_id": "q2", "likert_score": 5},
                ],
            },
        ]
        result = SurveyStatistics._demographic_cross_tabs(agents, ["q1", "q2"])
        assert len(result) >= 1
        age_tab = [t for t in result if t["field"] == "age"]
        assert len(age_tab) == 1
        groups = {g["group"]: g for g in age_tab[0]["groups"]}
        assert "young" in groups
        assert "old" in groups

    def test_cross_tabs_skips_single_group(self):
        agents = [
            {
                "persona": {"age": "same"},
                "responses": [{"question_id": "q1", "likert_score": 3}],
            },
            {
                "persona": {"age": "same"},
                "responses": [{"question_id": "q1", "likert_score": 4}],
            },
        ]
        result = SurveyStatistics._demographic_cross_tabs(agents, ["q1"])
        assert len([t for t in result if t["field"] == "age"]) == 0

    def test_cross_tabs_no_likert_ids(self):
        assert SurveyStatistics._demographic_cross_tabs([{"persona": {}}], []) == []


class TestComputeAll:
    def test_compute_all_with_results(self):
        results = {
            "total_agents": 2,
            "total_questions": 1,
            "likert_scale": 5,
            "results": [
                {
                    "persona": {"age": "young"},
                    "responses": [
                        {
                            "question_id": "q1",
                            "question": "Test?",
                            "likert_score": 4,
                            "answer": "4",
                        }
                    ],
                },
                {
                    "persona": {"age": "old"},
                    "responses": [
                        {
                            "question_id": "q1",
                            "question": "Test?",
                            "likert_score": 2,
                            "answer": "2",
                        }
                    ],
                },
            ],
        }
        stats = SurveyStatistics.compute_all(results)
        assert "descriptives" in stats
        assert "frequencies" in stats
        assert "summary" in stats
        assert stats["total_respondents"] == 2
        assert stats["likert_scale"] == 5

    def test_compute_all_empty(self):
        stats = SurveyStatistics.compute_all({"results": []})
        assert "error" in stats
