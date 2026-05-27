"""
PDF Renderer — Generates survey PDF reports using Jinja2 + WeasyPrint.
"""

import base64
import io
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.report.pdf')

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("weasyprint not installed, PDF generation disabled")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not installed, chart generation disabled")

REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'pdf_reports')


def _generate_bar_chart(qid: str, distribution: Dict, title: str, scale: int) -> Optional[str]:
    """Generate a bar chart and return as base64 PNG string."""
    if not MATPLOTLIB_AVAILABLE:
        return None
    try:
        labels = [str(i) for i in range(1, scale + 1)]
        values = [distribution.get(str(i), {}).get('count', 0) for i in range(1, scale + 1)]

        fig, ax = plt.subplots(figsize=(6, 2.5))
        colors = ['#1e293b' if v != max(values) else '#2563eb' for v in values]
        bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=0.5)

        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                        str(val), ha='center', va='bottom', fontsize=8, fontweight='bold')

        ax.set_xlabel('Skor Likert', fontsize=7)
        ax.set_ylabel('Frekuensi', fontsize=7)
        ax.set_title(title[:60], fontsize=9, fontweight='bold', pad=6)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='both', labelsize=7)
        ax.set_ylim(0, max(values) * 1.25 + 0.5 if values else 5)

        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        logger.warning(f"Chart generation failed for {qid}: {e}")
        return None


def _generate_interpretation(statistics: Dict[str, Any], survey_config: Optional[Dict] = None) -> str:
    """Generate plain-language interpretation of statistics."""
    summary = statistics.get('summary', {})
    base = summary.get('text', 'Hasil survei menunjukkan variasi respons di antara para responden.')

    descriptives = statistics.get('descriptives', {})
    if descriptives:
        means = [d['mean'] for d in descriptives.values() if 'mean' in d]
        if means:
            highest = max(descriptives.items(), key=lambda x: x[1].get('mean', 0))
            lowest = min(descriptives.items(), key=lambda x: x[1].get('mean', 0))
            base += (
                f"\n\nPertanyaan dengan tingkat persetujuan tertinggi adalah "
                f"\"{highest[1].get('question_text', highest[0])[:60]}\" "
                f"(Mean = {highest[1].get('mean', 0):.2f}). "
                f"Pertanyaan dengan tingkat persetujuan terendah adalah "
                f"\"{lowest[1].get('question_text', lowest[0])[:60]}\" "
                f"(Mean = {lowest[1].get('mean', 0):.2f})."
            )

    alpha = statistics.get('cronbach_alpha')
    if alpha is not None:
        if alpha >= 0.7:
            base += f"\n\nInstrumen survei memiliki konsistensi internal yang baik (α = {alpha:.3f}), menunjukkan bahwa pertanyaan-pertanyaan dalam survei ini reliabel dan dapat dipercaya."
        elif alpha >= 0.5:
            base += f"\n\nInstrumen survei memiliki konsistensi internal yang cukup (α = {alpha:.3f}), namun masih dapat ditingkatkan dengan merevisi beberapa pertanyaan."
        else:
            base += f"\n\nInstrumen survei memiliki konsistensi internal yang rendah (α = {alpha:.3f}). Disarankan untuk meninjau kembali pertanyaan-pertanyaan dalam survei."

    cross_tabs = statistics.get('cross_tabs', [])
    if cross_tabs:
        base += "\n\nAnalisis tabulasi silang menunjukkan variasi respons antar kelompok demografi:"
        for ct in cross_tabs:
            groups = ct.get('groups', [])
            if groups:
                max_g = max(groups, key=lambda g: g.get('mean', 0))
                min_g = min(groups, key=lambda g: g.get('mean', 0))
                field_label = {'age': 'usia', 'gender': 'gender', 'education': 'pendidikan', 'occupation': 'pekerjaan', 'personality': 'kepribadian'}
                base += f"\n- Berdasarkan {field_label.get(ct['field'], ct['field'])}: kelompok \"{max_g['group']}\" memiliki mean tertinggi ({max_g.get('mean', 0):.2f}) dan \"{min_g['group']}\" terendah ({min_g.get('mean', 0):.2f})."

    return base


def _generate_conclusion(statistics: Dict[str, Any], total_resp: int, total_q: int) -> str:
    """Generate overall conclusion."""
    lines = [
        f"Berdasarkan hasil analisis terhadap {total_resp} responden dengan {total_q} butir pertanyaan, "
        f"berikut adalah kesimpulan utama dari survei ini."
    ]

    descriptives = statistics.get('descriptives', {})
    if descriptives:
        means = [d['mean'] for d in descriptives.values() if 'mean' in d]
        if means:
            overall_mean = sum(means) / len(means)
            scale = statistics.get('likert_scale', 5)
            midpoint = (scale + 1) / 2
            direction = "cenderung positif/setuju" if overall_mean > midpoint else "cenderung negatif/tidak setuju" if overall_mean < midpoint else "berada pada titik netral"

            highest = max(descriptives.items(), key=lambda x: x[1].get('mean', 0))
            lowest = min(descriptives.items(), key=lambda x: x[1].get('mean', 0))
            lines.append(
                f"Secara keseluruhan, rata-rata skor jawaban responden adalah {overall_mean:.2f} dari skala {scale} "
                f"({direction}). Aspek dengan persetujuan tertinggi adalah "
                f"\"{highest[1].get('question_text', highest[0])}\" "
                f"(Mean = {highest[1].get('mean', 0):.2f}), sedangkan aspek dengan persetujuan terendah adalah "
                f"\"{lowest[1].get('question_text', lowest[0])}\" "
                f"(Mean = {lowest[1].get('mean', 0):.2f})."
            )

    alpha = statistics.get('cronbach_alpha')
    if alpha is not None:
        if alpha >= 0.7:
            lines.append(f"Instrumen survei memiliki reliabilitas yang baik (α = {alpha:.3f}), sehingga hasil yang diperoleh dapat dipercaya.")
        elif alpha >= 0.5:
            lines.append(f"Reliabilitas instrumen berada pada tingkat cukup (α = {alpha:.3f}). Beberapa pertanyaan mungkin perlu disesuaikan untuk meningkatkan konsistensi internal.")
        else:
            lines.append(f"Reliabilitas instrumen tergolong rendah (α = {alpha:.3f}). Disarankan untuk meninjau ulang konstruk pertanyaan pada survei selanjutnya.")

    cross_tabs = statistics.get('cross_tabs', [])
    if cross_tabs:
        lines.append("Analisis berdasarkan karakteristik demografi menunjukkan adanya perbedaan pola respons antar kelompok, yang menandakan bahwa latar belakang responden turut memengaruhi persepsi dan jawaban mereka.")

    lines.append(
        "Kesimpulan ini diharapkan dapat menjadi acuan bagi pengambil keputusan dalam menentukan langkah "
        "selanjutnya, baik untuk pengembangan instrumen maupun untuk tindakan lanjutan berdasarkan temuan survei."
    )

    return " ".join(lines)


def generate_pdf(
    project_id: str,
    results: Dict[str, Any],
    statistics: Dict[str, Any],
    survey_config: Optional[Dict] = None,
    report_data: Optional[Dict] = None
) -> str:
    """
    Generate a PDF report from survey data using Jinja2 + WeasyPrint.
    Returns path to the generated PDF file.
    """
    if not WEASYPRINT_AVAILABLE:
        raise RuntimeError("weasyprint is required for PDF generation")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    output_path = os.path.join(REPORTS_DIR, f"{project_id}.pdf")

    # ─── Prepare template data ───
    descriptives = statistics.get('descriptives', {})
    frequencies = statistics.get('frequencies', {})
    cross_tabs = statistics.get('cross_tabs', [])
    likert_scale = statistics.get('likert_scale', 5)
    total_respondents = statistics.get('total_respondents', 0)
    total_questions = statistics.get('total_questions', 0)
    alpha = statistics.get('cronbach_alpha')

    # Generate charts
    charts = {}
    for qid, freq in frequencies.items():
        if freq.get('type') == 'likert':
            dist = freq.get('distribution', {})
            q_text = freq.get('question_text', qid)
            chart_b64 = _generate_bar_chart(qid, dist, q_text, likert_scale)
            if chart_b64:
                charts[qid] = chart_b64

    # Generate interpretation & conclusion
    interpretation = _generate_interpretation(statistics, survey_config)
    conclusion = _generate_conclusion(statistics, total_respondents, total_questions)

    # Survey metadata
    survey_title = survey_config.get('title', 'Laporan Survei') if survey_config else 'Laporan Survei'
    survey_description = survey_config.get('description', '') if survey_config else ''
    sim_type = survey_config.get('sim_type', 'academic') if survey_config else 'academic'
    type_map = {'academic': 'Akademik', 'political': 'Politik', 'market': 'Pasar', 'social': 'Sosial', 'custom': 'Kustom'}
    sim_type_label = type_map.get(sim_type, sim_type)

    # ─── Render Jinja2 template ───
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report_survey.html')

    summary = statistics.get('summary', {})

    html_str = template.render(
        survey_title=survey_title,
        survey_description=survey_description,
        sim_type_label=sim_type_label,
        total_respondents=total_respondents,
        total_questions=total_questions,
        likert_scale=likert_scale,
        alpha=alpha,
        descriptives=descriptives,
        frequencies=frequencies,
        cross_tabs=cross_tabs,
        charts=charts,
        summary=summary,
        interpretation=interpretation,
        conclusion=conclusion,
        generated_date=datetime.now().strftime('%d %B %Y %H:%M'),
        report_data=report_data,
    )

    # ─── Convert to PDF ───
    HTML(string=html_str).write_pdf(output_path)
    logger.info(f"PDF report generated: {output_path}")
    return output_path


def get_report_path(project_id: str) -> Optional[str]:
    """Get path to a generated PDF report."""
    path = os.path.join(REPORTS_DIR, f"{project_id}.pdf")
    return path if os.path.exists(path) else None


def delete_report(project_id: str) -> bool:
    """Delete a generated PDF report."""
    path = get_report_path(project_id)
    if path:
        os.remove(path)
        return True
    return False