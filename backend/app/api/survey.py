"""
Academic Survey API routes
"""

import traceback
from flask import request, jsonify

from . import survey_bp
from ..services.survey_service import SurveyTemplateService, AcademicPersonaGenerator
from ..utils.logger import get_logger

logger = get_logger('kinjeng.api.survey')


@survey_bp.route('/templates', methods=['GET'])
def list_templates():
    """List available survey question type templates."""
    try:
        templates = SurveyTemplateService.get_available_templates()
        return jsonify({
            "success": True,
            "data": templates
        })
    except Exception as e:
        logger.error(f"Failed to list templates: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@survey_bp.route('/configure/<project_id>', methods=['POST'])
def save_survey_config(project_id: str):
    """Save survey configuration for a project."""
    try:
        data = request.get_json(force=True)
        filepath = SurveyTemplateService.save_survey_config(project_id, data)
        logger.info(f"Survey config saved for project {project_id}")
        return jsonify({
            "success": True,
            "data": {"filepath": filepath, "project_id": project_id}
        })
    except Exception as e:
        logger.error(f"Failed to save survey config: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@survey_bp.route('/configure/<project_id>', methods=['GET'])
def load_survey_config(project_id: str):
    """Load survey configuration for a project."""
    try:
        survey = SurveyTemplateService.load_survey_config(project_id)
        if survey is None:
            return jsonify({
                "success": False,
                "error": "No survey config found for this project"
            }), 404
        return jsonify({
            "success": True,
            "data": survey
        })
    except Exception as e:
        logger.error(f"Failed to load survey config: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@survey_bp.route('/personas/generate', methods=['POST'])
def generate_personas():
    """
    Generate academic survey agent personas.
    
    Body:
        count: int — Number of personas to generate (default 100)
    """
    try:
        data = request.get_json(force=True) if request.is_json else {}
        count = min(int(data.get('count', 100)), 10000)

        logger.info(f"Generating {count} academic personas")

        personas = AcademicPersonaGenerator.generate_batch(count)

        return jsonify({
            "success": True,
            "data": {
                "total": len(personas),
                "personas": personas[:100],
                "sample_size": min(count, 100)
            }
        })
    except Exception as e:
        logger.error(f"Persona generation failed: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@survey_bp.route('/prompts', methods=['GET'])
def get_academic_prompts():
    """Get the academic agent prompt templates."""
    try:
        prompts = SurveyTemplateService.get_academic_agent_prompt()
        return jsonify({
            "success": True,
            "data": prompts
        })
    except Exception as e:
        logger.error(f"Failed to get prompts: {e}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
