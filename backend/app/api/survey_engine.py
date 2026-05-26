"""
Survey Engine API — Full lifecycle: generate → run → analyze → results
"""

import json
import traceback
from flask import request, jsonify

from . import survey_bp
from ..services.survey_generator import SurveyGenerator, SurveyResultStore
from ..services.survey_statistics import SurveyStatistics
from ..services.survey_service import AcademicPersonaGenerator, SurveyTemplateService
from ..services.cognitive_pipeline import SurveyEngine
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.survey_engine')


@survey_bp.route('/generate', methods=['POST'])
def generate_survey():
    """
    Generate an academic survey from requirement + optional document context.
    
    Body:
        requirement: str (required) — Natural language research requirement
        sim_type: str — Simulation type (default: academic)
        params: dict — Survey parameters
        document_context: str (optional) — Extracted text from uploaded docs
    """
    try:
        data = request.get_json(force=True)
        requirement = data.get('requirement', '').strip()
        sim_type = data.get('sim_type', 'academic')
        params = data.get('params', {})
        document_context = data.get('document_context')

        if not requirement:
            return jsonify({"success": False, "error": "requirement is required"}), 400

        logger.info(f"Generating survey: type={sim_type}")
        survey = SurveyGenerator.generate(requirement, sim_type, params, document_context)

        return jsonify({
            "success": True,
            "data": survey
        })

    except Exception as e:
        logger.error(f"Survey generate failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/generate/enhance', methods=['POST'])
def enhance_survey():
    """
    Enhance an existing survey based on feedback.
    
    Body:
        survey: dict (required) — Existing survey config
        feedback: str (required) — User feedback / revision request
    """
    try:
        data = request.get_json(force=True)
        survey = data.get('survey', {})
        feedback = data.get('feedback', '').strip()

        if not survey or not feedback:
            return jsonify({"success": False, "error": "survey and feedback are required"}), 400

        enhanced = SurveyGenerator.enhance_existing(survey, feedback)

        return jsonify({
            "success": True,
            "data": enhanced
        })

    except Exception as e:
        logger.error(f"Survey enhance failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/run', methods=['POST'])
def run_survey():
    """
    Execute a complete survey simulation.
    
    Body:
        project_id: str (required)
        survey: dict (required) — Full survey config
        agent_count: int — Number of agent personas (default: 100)
        use_llm: bool — Use LLM for debate (default: false for speed)
        save_results: bool — Persist results (default: true)
    """
    try:
        data = request.get_json(force=True)
        project_id = data.get('project_id', '')
        survey_config = data.get('survey', {})
        agent_count = min(int(data.get('agent_count', 100)), 10000)
        use_llm = data.get('use_llm', False)
        save_results = data.get('save_results', True)

        if not project_id or not survey_config:
            return jsonify({"success": False, "error": "project_id and survey are required"}), 400

        logger.info(f"Running survey: project={project_id}, agents={agent_count}, llm={use_llm}")

        personas = AcademicPersonaGenerator.generate_batch(agent_count)

        engine = SurveyEngine(project_id, use_llm=use_llm)
        engine.load_survey(survey_config)
        engine.load_personas(personas)
        results = engine.run_survey()

        if save_results:
            SurveyResultStore.save(project_id, results)

        stats = SurveyStatistics.compute_all(results)

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "total_agents": results.get("total_agents"),
                "total_questions": results.get("total_questions"),
                "likert_scale": results.get("likert_scale"),
                "results": results.get("results", []),
                "statistics": stats
            }
        })

    except Exception as e:
        logger.error(f"Survey run failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/results/<project_id>', methods=['GET'])
def get_survey_results(project_id: str):
    """Get saved survey results."""
    try:
        results = SurveyResultStore.load(project_id)
        if results is None:
            return jsonify({"success": False, "error": "No results found"}), 404

        stats = SurveyStatistics.compute_all(results)

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "results": results,
                "statistics": stats
            }
        })

    except Exception as e:
        logger.error(f"Failed to load results: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/results/<project_id>/statistics', methods=['GET'])
def get_survey_statistics(project_id: str):
    """Get computed statistics from saved results."""
    try:
        results = SurveyResultStore.load(project_id)
        if results is None:
            return jsonify({"success": False, "error": "No results found"}), 404

        stats = SurveyStatistics.compute_all(results)

        return jsonify({
            "success": True,
            "data": stats
        })

    except Exception as e:
        logger.error(f"Failed to compute statistics: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/results', methods=['GET'])
def list_survey_results():
    """List all projects with saved survey results."""
    try:
        projects = SurveyResultStore.list()
        return jsonify({
            "success": True,
            "data": {"projects": projects, "total": len(projects)}
        })
    except Exception as e:
        logger.error(f"Failed to list results: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/results/<project_id>', methods=['DELETE'])
def delete_survey_results(project_id: str):
    """Delete saved survey results."""
    try:
        ok = SurveyResultStore.delete(project_id)
        if not ok:
            return jsonify({"success": False, "error": "No results found"}), 404
        return jsonify({"success": True, "message": f"Results deleted: {project_id}"})
    except Exception as e:
        logger.error(f"Failed to delete results: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
