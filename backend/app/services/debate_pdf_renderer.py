"""
Debate PDF Renderer — Generates debate session PDF reports using Jinja2 + WeasyPrint.
"""
import os
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('kinjeng.debate.pdf')

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("weasyprint not installed, debate PDF generation disabled")

REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'debate_pdfs')


def generate_debate_pdf(
    debate_id: str,
    question_text: str,
    likert_score: int,
    likert_scale: int = 5,
    confidence: float = 0.0,
    chairperson_conclusion: str = '',
    agents: list = None,
    posts: list = None,
    mode: str = 'auto'
) -> str:
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("weasyprint is required for PDF generation")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, f"{debate_id}.pdf")

    agents = agents or []
    posts = posts or []

    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('debate_report.html')

    html_str = template.render(
        question_text=question_text,
        likert_score=likert_score,
        likert_scale=likert_scale,
        confidence=confidence,
        chairperson_conclusion=chairperson_conclusion or '',
        agents=agents,
        posts=posts,
        mode=mode,
        generated_date=datetime.now().strftime('%d %B %Y %H:%M'),
    )

    HTML(string=html_str).write_pdf(output_path)
    logger.info(f"Debate PDF generated: {output_path}")
    return output_path


def get_debate_pdf_path(debate_id: str) -> str:
    path = os.path.join(REPORTS_DIR, f"{debate_id}.pdf")
    return path if os.path.exists(path) else None


def delete_debate_pdf(debate_id: str) -> bool:
    path = get_debate_pdf_path(debate_id)
    if path:
        os.remove(path)
        return True
    return False
