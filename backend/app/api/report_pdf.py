"""
PDF Report Generation API routes
"""

import os
import uuid
import traceback
from flask import request, jsonify, send_file

from . import survey_bp
from ..services import pdf_renderer
from ..services.survey_generator import SurveyResultStore
from ..services.survey_statistics import SurveyStatistics
from ..services.report_agent import ReportManager
from ..models.project import ProjectManager
from ..utils.logger import get_logger

logger = get_logger('kinjeng.api.report_pdf')


@survey_bp.route('/report/generate/<project_id>', methods=['POST'])
def generate_survey_report(project_id: str):
    """
    Generate a PDF report from saved survey results.
    
    Body (optional):
        survey_config: dict — The original survey config for title/metadata
        report_data: dict — Step4 report outline {title, summary, sections[]}
    """
    try:
        data = request.get_json(force=True) if request.is_json else {}
        survey_config = data.get('survey_config')
        report_data = data.get('report_data')

        results = SurveyResultStore.load(project_id)
        if results is None:
            return jsonify({"success": False, "error": "No survey results found"}), 404

        # Auto-lookup prediction report from project simulation
        prediction_report = None
        try:
            project = ProjectManager.get_project(project_id)
            if project and project.simulation_id:
                report = ReportManager.get_report_by_simulation(project.simulation_id)
                if report and report.outline:
                    outline_dict = report.outline.to_dict()
                    prediction_report = {
                        "title": outline_dict.get("title", "Laporan Prediksi Simulasi"),
                        "summary": outline_dict.get("summary", ""),
                        "sections": outline_dict.get("sections", []),
                        "full_content": report.markdown_content or ""
                    }
        except Exception as e:
            logger.warning(f"Prediction report lookup skipped: {e}")

        statistics = SurveyStatistics.compute_all(results)

        filepath = pdf_renderer.generate_pdf(
            project_id=project_id,
            results=results,
            statistics=statistics,
            survey_config=survey_config,
            report_data=report_data,
            prediction_report=prediction_report
        )

        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "filepath": filepath,
                "filename": f"{project_id}.pdf"
            }
        })

    except Exception as e:
        logger.error(f"PDF report generation failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/report/test', methods=['GET'])
def test_pdf_generation():
    """Test endpoint: generates a sample PDF to verify weasyprint works."""
    try:
        import io, json, random, os
        from datetime import datetime
        from ..config import Config
        from ..services.survey_statistics import SurveyStatistics

        project_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Create minimal fake survey results
        fake_results = {
            "project_id": project_id,
            "total_agents": 20,
            "total_questions": 3,
            "likert_scale": 5,
            "results": []
        }
        for i in range(20):
            agent = {
                "agent_id": f"agent_{i}",
                "persona": {
                    "age": random.choice([20,25,30,35,40]),
                    "occupation": random.choice(["Mahasiswa","Guru","Dokter","Insinyur"]),
                    "personality": random.choice(["Openness","Conscientiousness","Extraversion"]),
                    "gender": random.choice(["Laki-laki","Perempuan"])
                },
                "responses": [
                    {"question_id": "q01", "question": "Seberapa sering Anda menggunakan media sosial?", "answer": str(random.randint(1,5)), "likert_score": random.randint(1,5)},
                    {"question_id": "q02", "question": "Apakah media sosial mempengaruhi opini politik Anda?", "answer": str(random.randint(1,5)), "likert_score": random.randint(1,5)},
                    {"question_id": "q03", "question": "Seberapa percaya Anda dengan berita di media sosial?", "answer": str(random.randint(1,5)), "likert_score": random.randint(1,5)}
                ]
            }
            fake_results["results"].append(agent)

        statistics = SurveyStatistics.compute_all(fake_results)
        
        survey_config = {
            "title": "TEST: Dampak Media Sosial",
            "description": "PDF generation test",
            "sim_type": "academic",
            "sections": [
                {"id": "s1", "title": "Penggunaan Media Sosial", "questions": [
                    {"id": "q01", "text": "Seberapa sering Anda menggunakan media sosial?", "type": "likert", "scale": [1,2,3,4,5], "labels": ["Tidak pernah","Jarang","Kadang","Sering","Sangat sering"]},
                    {"id": "q02", "text": "Apakah media sosial mempengaruhi opini politik Anda?", "type": "likert", "scale": [1,2,3,4,5], "labels": ["Sangat tidak","Tidak","Netral","Ya","Sangat ya"]},
                    {"id": "q03", "text": "Seberapa percaya Anda dengan berita di media sosial?", "type": "likert", "scale": [1,2,3,4,5], "labels": ["Tidak percaya","Kurang","Cukup","Percaya","Sangat percaya"]}
                ]}
            ],
            "hypotheses": ["Media sosial meningkatkan polarisasi politik"],
            "demographics": [{"key": "Usia", "options": ["20-25","26-35","36-45"]}]
        }
        
        filepath = pdf_renderer.generate_pdf(
            project_id=project_id,
            results=fake_results,
            statistics=statistics,
            survey_config=survey_config,
            report_data=None,
            prediction_report=None
        )
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "filepath": filepath,
                "filename": f"{project_id}.pdf",
                "message": "PDF generated successfully! Download at: GET /api/survey/report/" + project_id
            }
        })
    except Exception as e:
        logger.error(f"Test PDF failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/report/<project_id>', methods=['GET'])
def download_survey_report(project_id: str):
    """Download a generated PDF report."""
    try:
        path = pdf_renderer.get_report_path(project_id)
        if path is None:
            return jsonify({"success": False, "error": "Report not found. Generate it first."}), 404

        return send_file(
            path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{project_id}.pdf"
        )

    except Exception as e:
        logger.error(f"PDF download failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500


@survey_bp.route('/report/<project_id>', methods=['DELETE'])
def delete_survey_report(project_id: str):
    """Delete a generated PDF report."""
    try:
        ok = pdf_renderer.delete_report(project_id)
        if not ok:
            return jsonify({"success": False, "error": "Report not found"}), 404
        return jsonify({"success": True, "message": f"Report deleted: {project_id}"})
    except Exception as e:
        logger.error(f"PDF delete failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
