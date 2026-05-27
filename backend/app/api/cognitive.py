"""
Cognitive Architecture API routes
Inner Parliament, Survey Memory, and Cognitive Pipeline
"""

import json
import traceback
from flask import request, jsonify

from . import cognitive_bp
from ..services.inner_parliament import InnerParliament, DEBATE_PERSPECTIVES
from ..services.survey_memory import SurveyMemory, SurveyMemoryStore
from ..services.cognitive_pipeline import CognitivePipeline, SurveyEngine
from ..services.survey_service import SurveyTemplateService, AcademicPersonaGenerator
from ..utils.logger import get_logger

logger = get_logger('kinjeng.api.cognitive')


@cognitive_bp.route('/parliament/perspectives', methods=['GET'])
def list_perspectives():
    """List all available debate perspectives."""
    data = {
        key: {"name": val["name"], "description": val["description"]}
        for key, val in DEBATE_PERSPECTIVES.items()
    }
    return jsonify({"success": True, "data": data})


@cognitive_bp.route('/parliament/debate', methods=['POST'])
def run_debate():
    """
    Run Inner Parliament debate for a single question + persona.
    
    Body:
        question: str (required)
        persona: dict (required) — Agent persona with age, gender, personality, etc.
        likert_scale: int (optional, default 5)
        use_llm: bool (optional, default true)
    """
    try:
        data = request.get_json(force=True)
        question = data.get('question', '').strip()
        persona = data.get('persona', {})
        likert_scale = int(data.get('likert_scale', 5))
        use_llm = data.get('use_llm', True)

        if not question or not persona:
            return jsonify({"success": False, "error": "question and persona are required"}), 400

        parliament = InnerParliament(use_llm=use_llm)
        debate_round = parliament.debate(question, persona, likert_scale)

        return jsonify({
            "success": True,
            "data": {
                "question": debate_round.question,
                "persona_summary": debate_round.persona_summary,
                "perspectives": {
                    k: {
                        "name": DEBATE_PERSPECTIVES.get(k, {}).get("name", k),
                        "response": v
                    }
                    for k, v in debate_round.perspectives.items()
                },
                "final_likert_score": debate_round.final_likert_score,
                "confidence": debate_round.confidence,
                "dominant_perspective": debate_round.dominant_perspective,
                "chairperson_synthesis": debate_round.chairperson_synthesis,
                "final_answer": debate_round.final_answer,
                "reasoning": debate_round.reasoning
            }
        })

    except Exception as e:
        logger.error(f"Debate failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@cognitive_bp.route('/pipeline/answer', methods=['POST'])
def pipeline_answer():
    """
    Process a question through the full cognitive pipeline.
    
    Body:
        agent_id: str (required)
        persona: dict (required)
        question: dict (required) — {id, text, type, options?, scale?}
        likert_scale: int (optional, default 5)
        use_llm: bool (optional, default true)
    """
    try:
        data = request.get_json(force=True)
        agent_id = data.get('agent_id', '')
        persona = data.get('persona', {})
        question = data.get('question', {})
        likert_scale = int(data.get('likert_scale', 5))
        use_llm = data.get('use_llm', True)

        if not agent_id or not persona or not question:
            return jsonify({"success": False, "error": "agent_id, persona, and question are required"}), 400

        pipeline = CognitivePipeline(use_llm=use_llm)
        response = pipeline.process_question(agent_id, persona, question, likert_scale=likert_scale)

        return jsonify({
            "success": True,
            "data": {
                "agent_id": response.agent_id,
                "question_id": response.question_id,
                "question": response.question_text,
                "answer": response.answer,
                "likert_score": response.likert_score,
                "text_answer": response.text_answer,
                "confidence": response.confidence,
                "processing_time_ms": round(response.processing_time_ms, 2),
                "error": response.error
            }
        })

    except Exception as e:
        logger.error(f"Pipeline answer failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@cognitive_bp.route('/pipeline/batch', methods=['POST'])
def pipeline_batch():
    """
    Process multiple questions for one agent.
    
    Body:
        agent_id: str (required)
        persona: dict (required)
        questions: list[dict] (required)
        likert_scale: int (optional, default 5)
        use_llm: bool (optional, default true)
    """
    try:
        data = request.get_json(force=True)
        agent_id = data.get('agent_id', '')
        persona = data.get('persona', {})
        questions = data.get('questions', [])
        likert_scale = int(data.get('likert_scale', 5))
        use_llm = data.get('use_llm', True)

        if not agent_id or not persona or not questions:
            return jsonify({"success": False, "error": "agent_id, persona, and questions are required"}), 400

        pipeline = CognitivePipeline(use_llm=use_llm)
        responses = pipeline.process_batch(agent_id, persona, questions, likert_scale=likert_scale)

        return jsonify({
            "success": True,
            "data": {
                "agent_id": agent_id,
                "total_questions": len(responses),
                "responses": [
                    {
                        "question_id": r.question_id,
                        "question": r.question_text,
                        "answer": r.answer,
                        "likert_score": r.likert_score,
                        "text_answer": r.text_answer,
                        "confidence": r.confidence,
                        "processing_time_ms": round(r.processing_time_ms, 2)
                    }
                    for r in responses
                ]
            }
        })

    except Exception as e:
        logger.error(f"Pipeline batch failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@cognitive_bp.route('/engine/run', methods=['POST'])
def run_survey_engine():
    """
    Run full survey simulation across multiple agents.
    
    Body:
        project_id: str (required)
        survey: dict (required) — Survey config with sections, questions, params
        personas: list[dict] (required) — Agent personas
        agent_ids: list[str] (optional) — Filter to specific agents
        question_ids: list[str] (optional) — Filter to specific questions
        use_llm: bool (optional, default false — rule-based for speed)
    """
    try:
        data = request.get_json(force=True)
        project_id = data.get('project_id', '')
        survey_config = data.get('survey', {})
        personas = data.get('personas', [])
        agent_ids = data.get('agent_ids')
        question_ids = data.get('question_ids')
        use_llm = data.get('use_llm', False)

        if not project_id or not survey_config or not personas:
            return jsonify({"success": False, "error": "project_id, survey, and personas are required"}), 400

        engine = SurveyEngine(project_id, use_llm=use_llm)
        engine.load_survey(survey_config)
        engine.load_personas(personas)
        results = engine.run_survey(question_ids=question_ids, agent_ids=agent_ids)

        return jsonify({
            "success": True,
            "data": {
                "project_id": results.get("project_id"),
                "total_agents": results.get("total_agents"),
                "total_questions": results.get("total_questions"),
                "likert_scale": results.get("likert_scale"),
                "results_count": len(results.get("results", [])),
                "results": results.get("results", [])
            }
        })

    except Exception as e:
        logger.error(f"Survey engine run failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@cognitive_bp.route('/memory/<agent_id>', methods=['GET'])
def get_agent_memory(agent_id: str):
    """Get stored memory for a specific agent."""
    try:
        memory = SurveyMemory(agent_id)
        return jsonify({
            "success": True,
            "data": memory.to_dict()
        })
    except Exception as e:
        logger.error(f"Failed to get memory: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@cognitive_bp.route('/memory/<agent_id>/add', methods=['POST'])
def add_agent_memory(agent_id: str):
    """
    Add a memory entry for an agent.
    
    Body:
        type: str — "episodic" | "semantic" | "reflective"
        content: str — Memory content
        question_id: str (optional) — For episodic memories
        answer: str (optional) — For episodic memories
        likert_score: int (optional)
    """
    try:
        data = request.get_json(force=True)
        mem_type = data.get('type', 'episodic')
        content = data.get('content', '').strip()

        if not content:
            return jsonify({"success": False, "error": "content is required"}), 400

        memory = SurveyMemory(agent_id)
        if mem_type == 'episodic':
            memory.add_episodic(
                question=content,
                answer=data.get('answer', ''),
                question_id=data.get('question_id'),
                likert_score=data.get('likert_score')
            )
        elif mem_type == 'semantic':
            memory.add_semantic(content)
        elif mem_type == 'reflective':
            memory.add_reflective(content)
        else:
            return jsonify({"success": False, "error": f"Unknown type: {mem_type}"}), 400

        memory.save()
        return jsonify({"success": True, "data": memory.to_dict()})

    except Exception as e:
        logger.error(f"Failed to add memory: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@cognitive_bp.route('/memory/<agent_id>/delete', methods=['DELETE'])
def delete_agent_memory(agent_id: str):
    """Delete all memory for an agent."""
    try:
        import os
        from ..config import Config
        path = os.path.join(Config.UPLOAD_FOLDER, 'survey_memories', f"{agent_id}.json")
        if os.path.exists(path):
            os.remove(path)
            return jsonify({"success": True, "message": f"Memory deleted for {agent_id}"})
        return jsonify({"success": False, "error": f"No memory found for {agent_id}"}), 404
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
