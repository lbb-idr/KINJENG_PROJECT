"""
PDF Report Generation API routes
"""

import os
import traceback
from flask import request, jsonify, send_file

from . import survey_bp
from ..services.report_generator_pdf import PDFReportGenerator
from ..services.survey_generator import SurveyResultStore
from ..services.survey_statistics import SurveyStatistics
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.report_pdf')


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

        statistics = SurveyStatistics.compute_all(results)

        filepath = PDFReportGenerator.generate(
            project_id=project_id,
            results=results,
            statistics=statistics,
            survey_config=survey_config,
            report_data=report_data
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


@survey_bp.route('/report/<project_id>', methods=['GET'])
def download_survey_report(project_id: str):
    """Download a generated PDF report."""
    try:
        path = PDFReportGenerator.get_report_path(project_id)
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
        ok = PDFReportGenerator.delete_report(project_id)
        if not ok:
            return jsonify({"success": False, "error": "Report not found"}), 404
        return jsonify({"success": True, "message": f"Report deleted: {project_id}"})
    except Exception as e:
        logger.error(f"PDF delete failed: {e}\n{traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e)}), 500
