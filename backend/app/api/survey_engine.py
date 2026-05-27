"""
Survey Engine API — Full lifecycle: generate → run → analyze → results
"""

import json
import os
import traceback
import uuid
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

        # Try to load real simulation agents first
        personas = None
        try:
            from ..services.simulation_manager import SimulationManager
            from ..models.project import ProjectManager
            manager = SimulationManager()
            project_mgr = ProjectManager()
            project = project_mgr.get_project(project_id)
            if project and getattr(project, 'simulation_id', None):
                profiles = manager.get_profiles(project.simulation_id, platform='reddit')
                if not profiles:
                    profiles = manager.get_profiles(project.simulation_id, platform='twitter')
                if profiles:
                    topic = survey_config.get("title", "") or survey_config.get("description", "")
                    personas = AcademicPersonaGenerator.map_simulation_to_survey(profiles[:agent_count], topic)
                    logger.info(f"Loaded {len(personas)} real simulation agents for survey")
        except Exception as e:
            logger.warning(f"Could not load simulation agents: {e}, falling back to generated batch")

        if not personas:
            personas = AcademicPersonaGenerator.generate_batch(agent_count)
            logger.info(f"Generated {len(personas)} random agent personas for survey")

        engine = SurveyEngine(project_id, use_llm=use_llm, agent_profiles=personas)
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


@survey_bp.route('/questions/<project_id>', methods=['POST'])
def save_custom_questions(project_id: str):
    """Save custom survey questions for a project."""
    try:
        data = request.get_json(force=True)
        questions_dir = os.path.join(SurveyResultStore.RESULTS_DIR, project_id)
        os.makedirs(questions_dir, exist_ok=True)
        path = os.path.join(questions_dir, 'questions.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({"success": True, "message": "Questions saved"})
    except Exception as e:
        logger.error(f"Save questions failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/questions/<project_id>', methods=['GET'])
def load_custom_questions(project_id: str):
    """Load saved custom questions for a project."""
    try:
        path = os.path.join(SurveyResultStore.RESULTS_DIR, project_id, 'questions.json')
        if not os.path.exists(path):
            return jsonify({"success": False, "error": "No custom questions"}), 404
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Load questions failed: {e}\n{traceback.format_exc()}")
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


# ====== Multi-Agent Debate Endpoints ======

@survey_bp.route('/debate/start', methods=['POST'])
def start_debate():
    """
    Start a multi-agent debate for one survey question.
    
    Body:
        project_id: str (optional) — jika ada, pakai simulation profiles
        question_id: str (optional) — auto-gen jika tidak ada
        question_text: str (required)
        likert_scale: int (default: 5)
        agent_count: int (default: 5)
        agents: list (optional) — manual agent definitions, skip auto-selection
    """
    try:
        data = request.get_json() or {}
        project_id = data.get('project_id')
        question_id = data.get('question_id') or f"q_{uuid.uuid4().hex[:6]}"
        question_text = data.get('question_text', '').strip()
        likert_scale = data.get('likert_scale', 5)
        agent_count = data.get('agent_count', 5)
        manual_agents = data.get('agents')

        if not question_text:
            return jsonify({"success": False, "error": "question_text required"}), 400

        from ..services.survey_debate import SurveyDebateService
        debate_svc = SurveyDebateService()

        if manual_agents and len(manual_agents) > 0:
            # Manual mode: gunakan agent yg dikirim user langsung
            selected = manual_agents[:agent_count]
        else:
            # Auto mode: cari agen relevan dari pool besar
            profiles = None
            if project_id:
                from ..services.simulation_manager import SimulationManager
                manager = SimulationManager()
                project_mgr = __import__('app.models.project', fromlist=['ProjectManager']).ProjectManager()
                project = project_mgr.get_project(project_id)
                if project and project.simulation_id:
                    sim_state = manager.get_simulation(project.simulation_id)
                    if sim_state:
                        profiles = manager.get_profiles(project.simulation_id, platform='reddit')
                        if not profiles:
                            profiles = manager.get_profiles(project.simulation_id, platform='twitter')

            if not profiles:
                # Generate pool besar (50), lalu pilih 5 paling relevan
                from ..services.survey_service import AcademicPersonaGenerator
                pool_size = max(agent_count * 10, 50)
                raw_personas = AcademicPersonaGenerator.generate_batch(pool_size)
                profiles = [{
                    "user_id": p.get("agent_id", f"agent_{i}"),
                    "name": f"Agent-{p.get('agent_id', '?')}",
                    "username": p.get("agent_id", f"agent_{i}"),
                    "age": p.get("age", 30),
                    "occupation": p.get("occupation", ""),
                    "profession": p.get("occupation", ""),
                    "personality": p.get("personality", ""),
                    "mbti": p.get("personality", ""),
                    "opinion_bias": p.get("opinion_bias", "Seimbang"),
                    "bio": f"Usia {p.get('age', '?')}, {p.get('occupation', '?')}, {p.get('personality', '?')}"
                } for i, p in enumerate(raw_personas)]

            # Pilih agen paling relevan berdasarkan keyword matching
            selected = debate_svc.select_debate_agents(question_text, profiles, count=agent_count)

        # Create session
        session = debate_svc.create_session(question_id, question_text, selected, likert_scale)

        return jsonify({
            "success": True,
            "data": {
                "session_id": session.session_id,
                "question_id": session.question_id,
                "question_text": session.question_text,
                "agent_count": len(session.agents),
                "confirmed_count": 0,
                "agents": [
                    {"id": a.get("user_id"), "name": a.get("name", a.get("username", "?")), "age": a.get("age"), "occupation": a.get("occupation", a.get("profession", "")), "personality": a.get("personality", a.get("mbti", "")), "opinion_bias": a.get("opinion_bias", ""), "bio": a.get("bio", "")}
                    for a in session.agents
                ],
                "status": session.status
            }
        })

    except Exception as e:
        logger.error(f"Start debate failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/debate/<session_id>/confirm', methods=['POST'])
def confirm_debate_agent(session_id: str):
    """Confirm the next unconfirmed agent for a debate session."""
    try:
        from ..services.survey_debate import SurveyDebateService
        debate_svc = SurveyDebateService()
        session = debate_svc.confirm_agent(session_id)

        return jsonify({
            "success": True,
            "data": {
                "session_id": session.session_id,
                "status": session.status,
                "confirmed_count": session.confirmed_count,
                "total_agents": len(session.agents),
                "current_agent": session.agents[session.confirmed_count - 1] if session.confirmed_count > 0 else None
            }
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Confirm agent failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/debate/<session_id>/run', methods=['POST'])
def run_debate(session_id: str):
    """Run all debate rounds for a session (synchronous). Returns all posts + result."""
    try:
        from ..services.survey_debate import SurveyDebateService
        debate_svc = SurveyDebateService()
        session = debate_svc.run_debate(session_id)

        return jsonify({
            "success": True,
            "data": {
                "session_id": session.session_id,
                "question_id": session.question_id,
                "question_text": session.question_text,
                "status": session.status,
                "likert_score": session.likert_score,
                "confidence": session.confidence,
                "chairperson_conclusion": session.chairperson_conclusion,
                "likert_scale": session.likert_scale,
                "agents": [
                    {"id": a.get("user_id"), "name": a.get("name", a.get("username", "?"))}
                    for a in session.agents
                ],
                "posts": [
                    {
                        "round_num": p.round_num,
                        "agent_id": p.agent_id,
                        "agent_name": p.agent_name,
                        "content": p.content,
                        "timestamp": p.timestamp
                    }
                    for p in session.posts
                ]
            }
        })

    except Exception as e:
        logger.error(f"Run debate failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/debate/<session_id>', methods=['GET'])
def get_debate_session(session_id: str):
    """Get current debate session state (for frontend polling)."""
    try:
        from ..services.survey_debate import SurveyDebateService
        debate_svc = SurveyDebateService()
        session = debate_svc.get_session(session_id)
        if not session:
            return jsonify({"success": False, "error": "Session not found"}), 404

        return jsonify({
            "success": True,
            "data": {
                "session_id": session.session_id,
                "question_id": session.question_id,
                "question_text": session.question_text,
                "status": session.status,
                "likert_score": session.likert_score,
                "confidence": session.confidence,
                "chairperson_conclusion": session.chairperson_conclusion,
                "likert_scale": session.likert_scale,
                "confirmed_count": session.confirmed_count,
                "agents": [
                    {"id": a.get("user_id"), "name": a.get("name", a.get("username", "?")), "age": a.get("age"), "occupation": a.get("occupation", a.get("profession", "")), "personality": a.get("personality", a.get("mbti", "")), "opinion_bias": a.get("opinion_bias", ""), "bio": a.get("bio", "")}
                    for a in session.agents
                ],
                "posts": [
                    {
                        "round_num": p.round_num,
                        "agent_id": p.agent_id,
                        "agent_name": p.agent_name,
                        "content": p.content,
                        "timestamp": p.timestamp
                    }
                    for p in session.posts
                ]
            }
        })

    except Exception as e:
        logger.error(f"Get debate session failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/debate/run-all', methods=['POST'])
def run_all_debates():
    """
    Run debates for ALL questions in a survey.
    Body:
        project_id: str
        survey: dict (the full survey config)
        agent_count: int (default: 5)
    Returns list of session IDs and questions — frontend polls each session.
    """
    try:
        data = request.get_json() or {}
        project_id = data.get('project_id')
        survey = data.get('survey')
        agent_count = data.get('agent_count', 5)

        if not all([project_id, survey]):
            return jsonify({"success": False, "error": "project_id and survey required"}), 400

        # Load agents
        from ..services.simulation_manager import SimulationManager
        manager = SimulationManager()
        project_mgr = __import__('app.models.project', fromlist=['ProjectManager']).ProjectManager()
        project = project_mgr.get_project(project_id)
        if not project or not project.simulation_id:
            return jsonify({"success": False, "error": "No simulation"}), 400

        profiles = manager.get_profiles(project.simulation_id, platform='reddit')
        if not profiles:
            profiles = manager.get_profiles(project.simulation_id, platform='twitter')
        if not profiles:
            return jsonify({"success": False, "error": "No agent profiles"}), 404

        from ..services.survey_debate import SurveyDebateService
        debate_svc = SurveyDebateService()
        sessions = []

        questions = [
            q for section in survey.get("sections", [])
            for q in section.get("questions", [])
            if q.get("type") == "likert"
        ]

        for q in questions:
            qid = q.get("id", "q_unknown")
            qtext = q.get("text", "")
            agents = debate_svc.select_debate_agents(qtext, profiles, count=agent_count)
            session = debate_svc.create_session(qid, qtext, agents, survey.get("params", {}).get("likertScale", 5))
            result = debate_svc.run_debate(session.session_id)
            sessions.append({
                "session_id": result.session_id,
                "question_id": result.question_id,
                "question_text": result.question_text,
                "likert_score": result.likert_score,
                "confidence": result.confidence,
                "status": result.status
            })

        return jsonify({
            "success": True,
            "data": {
                "total_questions": len(questions),
                "sessions": sessions
            }
        })

    except Exception as e:
        logger.error(f"Run all debates failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
